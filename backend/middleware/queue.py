# backend/middleware/queue.py
import time
import asyncio
import httpx
import json
from agents.models import APIRequestLog, RequestBatch

def convert_body_json_to_safe_format(body_json) -> str:
    """
    Convert JSON body to a flattened, escape-safe format: key=value;key2=value2
    Handles nested objects and arrays by flattening them with dot notation.
    """
    if not body_json:
        return ""
    
    # If it's a string, try to parse it as JSON
    if isinstance(body_json, str):
        try:
            body_json = json.loads(body_json)
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, just escape and return as-is
            return body_json.replace(";", "\\;").replace("=", "\\=")
    
    # If it's not a dict, convert to string
    if not isinstance(body_json, dict):
        return str(body_json).replace(";", "\\;").replace("=", "\\=")
    
    def flatten_dict(d, parent_key='', sep='.'):
        """Recursively flatten nested dictionaries and lists."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to comma-separated values or flatten if list contains dicts
                if v and isinstance(v[0], dict):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                        else:
                            items.append((f"{new_key}[{i}]", str(item)))
                else:
                    items.append((new_key, ",".join(str(x) for x in v)))
            else:
                items.append((new_key, str(v)))
        return dict(items)
    
    # Flatten the dictionary
    flattened = flatten_dict(body_json)
    
    result_parts = []
    for key, value in flattened.items():
        result_parts.append(f"{key}={value}")
    
    return ";".join(result_parts)


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
            json_body=convert_body_json_to_safe_format(req.get("body_json", ""))
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