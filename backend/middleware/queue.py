# backend/middleware/queue.py
import time
import asyncio
import httpx
from agents.models import APIRequestLog, RequestBatch

# Global queue for request batching
request_queue = asyncio.Queue()
_processor_task = None

async def process_batch(batch: list):
    """
    Send batched requests to the Orchestrator agent using proper uAgents protocol.
    """
    print(f"Processing batch of {len(batch)} requests")

    # Convert middleware logs to agent message format
    request_logs = []
    for req in batch:
        log = APIRequestLog(
            ip_address=req.get("client_ip"),
            path=req.get("path", ""),
            method=req.get("method", ""),
            user_id=req.get("user"),
            json_body=str(req.get("body_json", ""))
        )
        request_logs.append(log)

    # Create the batch message
    batch_msg = RequestBatch(requests=request_logs)

    try:
        ORCHESTRATOR_URL = "http://localhost:8001/rest/post"
        try:
            async with httpx.AsyncClient() as client:
                # Serialize the batch message
                if hasattr(batch_msg, 'model_dump'):
                    payload = batch_msg.model_dump()
                else:
                    payload = batch_msg.dict()

                resp = await client.post(
                    ORCHESTRATOR_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            if resp.status_code == 200:
                print(f"✓ Sent batch of {len(request_logs)} requests to orchestrator via HTTP POST")
            else:
                print(f"✗ Failed to send batch: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"✗ Error sending to orchestrator: {e}")

    except Exception as e:
        print(f"✗ Error sending to orchestrator: {e}")


async def queue_processor():
    """
    Background task that processes the queue every 2 seconds or at 100 requests.
    """
    batch = []
    last_process_time = time.time()

    while True:
        try:
            # Wait up to 1 second for a new item
            try:
                item = await asyncio.wait_for(request_queue.get(), timeout=1.0)
                batch.append(item)
            except asyncio.TimeoutError:
                pass

            current_time = time.time()
            time_elapsed = current_time - last_process_time

            # Process if batch is full or 2 seconds have passed
            if len(batch) >= 100 or (len(batch) > 0 and time_elapsed >= 2.0):
                asyncio.create_task(process_batch(batch))
                batch = []
                last_process_time = current_time

        except Exception as e:
            print(f"Error in queue processor: {e}")
            await asyncio.sleep(1)

def start_queue_processor():
    """
    Start the background queue processor if not already running.
    """
    global _processor_task
    if _processor_task is None:
        asyncio.create_task(queue_processor())
        print("Queue processor started")