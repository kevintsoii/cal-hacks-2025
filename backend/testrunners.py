from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import logging
import asyncio
import httpx
from typing import Dict, List, Optional

# Import test configuration
from tests.config import RequestConfig

# Import test functions
from tests.auth import run_admin_100_test, run_admin_1000_test, run_credential_stuffing_test
from tests.search import run_admin_search_test, run_scraping_pattern_test, run_sql_injection_test

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Store active websocket connections
active_connections: Dict[str, WebSocket] = {}


class TestRequest(BaseModel):
    test_id: str


@router.websocket("/ws/test/{test_id}")
async def websocket_test_endpoint(websocket: WebSocket, test_id: str):
    """
    WebSocket endpoint for real-time test execution updates.
    """
    from starlette.websockets import WebSocketState
    
    await websocket.accept()
    active_connections[test_id] = websocket
    test_task = None
    # Create cancellation event here so we can set it immediately on disconnect
    cancellation_event = asyncio.Event()
    
    try:
        # Create a task for the test execution so we can cancel it if needed
        async def execute_test():
            # Execute the appropriate test
            if test_id == "admin-100":
                await run_admin_100_test(websocket, cancellation_event, execute_test_requests)
            elif test_id == "admin-1000":
                await run_admin_1000_test(websocket, cancellation_event, execute_test_requests)
            elif test_id == "credential-stuffing":
                await run_credential_stuffing_test(websocket, cancellation_event, execute_test_requests)
            elif test_id == "admin-search":
                await run_admin_search_test(websocket, cancellation_event, execute_test_requests)
            elif test_id == "scraping-pattern":
                await run_scraping_pattern_test(websocket, cancellation_event, execute_test_requests)
            elif test_id == "sql-injection":
                await run_sql_injection_test(websocket, cancellation_event, execute_test_requests)
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Test {test_id} not implemented yet"
                })
        
        # Start the test execution task
        test_task = asyncio.create_task(execute_test())
        
        # Create a task to listen for abort messages from the client
        async def listen_for_abort():
            try:
                while True:
                    message = await websocket.receive_json()
                    if message.get("type") == "abort":
                        logger.info(f"Received explicit abort message for test: {test_id}")
                        # IMMEDIATELY set the cancellation event
                        cancellation_event.set()
                        # Cancel the test task
                        if test_task and not test_task.done():
                            test_task.cancel()
                        break
            except Exception as e:
                logger.debug(f"Listener stopped: {e}")
        
        # Start the listener task
        listener_task = asyncio.create_task(listen_for_abort())
        
        # Wait for either the test to complete or abort signal
        done, pending = await asyncio.wait(
            [test_task, listener_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel any remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Send completion message only if WebSocket is still connected
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({
                "type": "completed",
                "message": "Test execution completed"
            })
            
            # Give client time to receive the message before closing
            await asyncio.sleep(0.1)
            
            # Properly close the WebSocket connection from server side
            await websocket.close()
            logger.info(f"WebSocket closed for test: {test_id}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for test: {test_id} - IMMEDIATE ABORT")
        # IMMEDIATELY set the cancellation event to stop any pending HTTP requests
        cancellation_event.set()
        # Cancel the test execution task
        if test_task and not test_task.done():
            test_task.cancel()
            try:
                await test_task
            except asyncio.CancelledError:
                logger.info(f"Test task {test_id} cancelled successfully")
    except Exception as e:
        logger.error(f"Error in WebSocket for test {test_id}: {e}")
        # IMMEDIATELY set the cancellation event
        cancellation_event.set()
        # Cancel the test execution task
        if test_task and not test_task.done():
            test_task.cancel()
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                await asyncio.sleep(0.1)
                await websocket.close()
        except:
            pass
    finally:
        if test_id in active_connections:
            del active_connections[test_id]


async def execute_test_requests(
    websocket: WebSocket,
    requests: List[RequestConfig],
    cancellation_event: asyncio.Event,
    max_concurrent: int = 2,
    delay_between_requests: float = 0.25
):
    """
    Generic function to execute a list of HTTP requests with WebSocket progress updates.
    
    Args:
        websocket: WebSocket connection for sending progress updates
        requests: List of RequestConfig objects defining the requests to make
        cancellation_event: Event to signal immediate cancellation of all requests
        max_concurrent: Maximum number of concurrent requests
        delay_between_requests: Delay in seconds between requests
    """
    from starlette.websockets import WebSocketState
    
    total_requests = len(requests)
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Helper function to safely send WebSocket messages
    async def safe_send_json(data: dict) -> bool:
        """Safely send JSON data via WebSocket. Returns True if successful, False if connection is closed."""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(data)
                return True
            return False
        except Exception as e:
            logger.debug(f"Failed to send WebSocket message: {e}")
            return False
    
    async def make_request(request_num: int, config: RequestConfig):
        async with semaphore:
            try:
                # Check if cancellation has been requested
                if cancellation_event.is_set():
                    logger.info(f"Cancellation detected, skipping request {request_num}")
                    return None
                
                # Check if WebSocket is still connected before making the request
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.info(f"WebSocket disconnected, skipping request {request_num}")
                    return None
                
                async with httpx.AsyncClient() as client:
                    # Double-check cancellation right before making the HTTP request
                    if cancellation_event.is_set():
                        logger.info(f"Cancellation detected before HTTP request {request_num}")
                        return None
                    
                    # Make the HTTP request based on config
                    request_kwargs = {
                        "url": config.url,
                        "timeout": config.timeout,
                    }
                    
                    if config.json_body:
                        request_kwargs["json"] = config.json_body
                    
                    if config.headers:
                        request_kwargs["headers"] = config.headers
                    
                    # Execute the request based on method
                    if config.method.upper() == "GET":
                        response = await client.get(**request_kwargs)
                    elif config.method.upper() == "POST":
                        response = await client.post(**request_kwargs)
                    elif config.method.upper() == "PUT":
                        response = await client.put(**request_kwargs)
                    elif config.method.upper() == "DELETE":
                        response = await client.delete(**request_kwargs)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {config.method}")
                    
                    await asyncio.sleep(delay_between_requests)
                    
                    # Send progress update via WebSocket (safely)
                    await safe_send_json({
                        "type": "progress",
                        "request_num": request_num,
                        "total": total_requests,
                        "status_code": response.status_code,
                        "url": config.url,
                        "method": config.method,
                        "ip": config.headers.get("mock-ip") if config.headers else None,
                        "success": response.status_code == 200
                    })
                    
                    return response.status_code
                    
            except asyncio.CancelledError:
                logger.info(f"Request {request_num} cancelled")
                raise  # Re-raise to properly propagate cancellation
            except Exception as e:
                logger.error(f"Error in request {request_num}: {e}")
                await safe_send_json({
                    "type": "progress",
                    "request_num": request_num,
                    "total": total_requests,
                    "status_code": 0,
                    "error": str(e),
                    "success": False
                })
                return 0
    
    # Execute all requests concurrently (with semaphore limiting concurrency)
    tasks = [asyncio.create_task(make_request(i + 1, req)) for i, req in enumerate(requests)]
    
    try:
        # Use return_exceptions=False so CancelledError propagates
        results = await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Test execution cancelled - signaling all tasks to stop")
        # Set the cancellation event to stop new HTTP requests from being made
        cancellation_event.set()
        # Cancel all pending tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for all tasks to finish cancelling
        await asyncio.gather(*tasks, return_exceptions=True)
        raise  # Re-raise the CancelledError
    
    # Filter out None results (from skipped requests)
    valid_results = [r for r in results if r is not None]
    
    # Send summary only if WebSocket is still connected
    if websocket.client_state == WebSocketState.CONNECTED:
        successful = sum(1 for r in valid_results if r == 200)
        failed = len(valid_results) - successful
        
        await safe_send_json({
            "type": "summary",
            "total": total_requests,
            "successful": successful,
            "failed": failed,
            "skipped": total_requests - len(valid_results)
        })