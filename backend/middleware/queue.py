import time
import asyncio


# Global queue for request batching
request_queue = asyncio.Queue()
_processor_task = None


async def process_batch(batch: list):
    """
    Skeleton processor function that will handle batched requests.
    """
    print(f"Processing batch of {len(batch)} requests")
    # TODO: Send to AI agent pipeline
    # TODO: Send to Elasticsearch
    pass


async def queue_processor():
    """
    Background task that processes queued requests either:
    - Every 2.5 seconds, OR
    - When batch reaches 100 items
    """
    batch = []
    last_process_time = time.time()
    
    while True:
        try:
            # Wait for items with timeout (2.5 seconds)
            try:
                item = await asyncio.wait_for(request_queue.get(), timeout=2.5)
                batch.append(item)
            except asyncio.TimeoutError:
                # 2.5 seconds passed, process whatever we have
                pass
            
            current_time = time.time()
            time_since_last_process = current_time - last_process_time
            
            # Process if: batch has 100 items OR 2.5 seconds have passed (and batch is not empty)
            should_process = len(batch) >= 100 or (time_since_last_process >= 2.5 and len(batch) > 0)
            
            if should_process:
                # Start batch processing in background without waiting
                asyncio.create_task(process_batch(batch))
                batch = []
                last_process_time = current_time
                
        except Exception as e:
            print(f"Error in queue processor: {e}")
            # Continue processing even if there's an error


def start_queue_processor():
    """
    Starts the queue processor background task if not already running.
    """
    global _processor_task
    if _processor_task is None:
        _processor_task = asyncio.create_task(queue_processor())