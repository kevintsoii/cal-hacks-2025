import time
import json
import hashlib
import asyncio
import os
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from .queue import request_queue, start_queue_processor
from .mitigation import check_mitigations, apply_mitigation
from db.elasticsearch import elasticsearch_client
from db.redis import redis_client


async def send_to_elasticsearch_and_websocket(request_info: dict):
    """
    Background task to send request data to Elasticsearch and broadcast via WebSocket.
    Non-blocking and fire-and-forget.
    """
    try:
        # Send to Elasticsearch
        await elasticsearch_client.index_document(
            index_name="api_requests",
            document=request_info
        )
        
        # Broadcast to WebSocket clients
        try:
            # Import here to avoid circular dependency
            from main import broadcast_new_request
            await broadcast_new_request(request_info)
        except Exception as ws_error:
            print(f"Error broadcasting to WebSocket: {ws_error}")
            
    except Exception as e:
        print(f"Error sending to Elasticsearch: {e}")


def sanitize_sensitive_data(data):
    """
    Sanitizes sensitive fields using deterministic hashing.
    This allows AI to detect if the same value is being spammed
    without exposing the actual sensitive data.
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = data.copy()
    sensitive_keys = ['password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey']
    
    for key, value in sanitized.items():
        key_lower = key.lower()
        # Check if key contains sensitive terms
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 0:
                # Create deterministic hash - same value = same hash
                hash_obj = hashlib.sha256(value.encode())
                hash_hex = hash_obj.hexdigest()[:16]  # First 16 chars of hash
                # Include length for additional pattern analysis
                sanitized[key] = f"hash_{hash_hex}_len{len(value)}"
            else:
                sanitized[key] = "hash_empty"
        # Recursively sanitize nested objects
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)
    
    return sanitized


class AIMiddleware(BaseHTTPMiddleware):
    """
    AI-powered security middleware that captures all relevant request information
    for threat detection and analysis.
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Start the queue processor on initialization
        start_queue_processor()
    
    async def dispatch(self, request: Request, call_next):
        # Extract IP immediately for mitigation check
        client_ip = request.client.host if request.client else None
        # Override with mock-ip header if provided (for testing)
        if "mock-ip" in request.headers:
            client_ip = request.headers.get("mock-ip")
        

        # Start timing
        start_time = time.time()
        timestamp = datetime.now(tz=timezone.utc).isoformat()

                # Extract comprehensive request info for AI security analysis
        request_info = {
            # Basic request info
            "timestamp": timestamp,
            "method": request.method,
            "path": request.url.path,
            "full_url": str(request.url),
            "query_params": dict(request.query_params) if request.query_params else None,
            
            # Client identification
            "client_ip": client_ip,
            "client_port": request.client.port if request.client else None,
            
            # Headers - security relevant
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
            "origin": request.headers.get("origin"),
            "content_type": request.headers.get("content-type"),
            "accept": request.headers.get("accept"),
            "authorization": None,  # Will be masked below
            "x_forwarded_for": request.headers.get("x-forwarded-for"),
            "x_real_ip": request.headers.get("x-real-ip"),
            
            # Cookies - just track presence, not values
            "cookies": list(request.cookies.keys()) if request.cookies else None,
            
            # Request body (will be populated below)
            "body_raw": None,
            "body_json": None,  # Parsed JSON for structured querying in ES
            "body_size": 0,

            "user": None,
        }

        # Read body once for both mitigation check and logging
        username = None
        captcha_token = None
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode()
                    request_info["body_raw"] = body_str
                    request_info["body_size"] = len(body)
                    try:
                        body_json = json.loads(body_str)
                        username = body_json.get("username") or body_json.get("yourUsername")
                        captcha_token = body_json.get("captcha_token")
                        request_info["body_json"] = sanitize_sensitive_data(body_json)

                        request_info["user"] = username
                    
                    except json.JSONDecodeError:
                        pass
                
                # Reset the request body stream so the route can read it
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception as e:
                request_info["body_error"] = str(e)
        
        # Check Redis for active mitigations (IP and User)
        severity = await check_mitigations(client_ip, username)
        
        # Apply mitigation if exists
        if severity > 0:
            mitigation_response = await apply_mitigation(severity, captcha_token)
            if mitigation_response:
                return mitigation_response
            # If no response (captcha verified or delay applied), continue processing
        
        
        # Hash authorization header (deterministic for spam detection)
        auth_header = request.headers.get("authorization")
        if auth_header:
            hash_obj = hashlib.sha256(auth_header.encode())
            hash_hex = hash_obj.hexdigest()[:16]
            request_info["authorization"] = f"hash_{hash_hex}_len{len(auth_header)}"
        
        # Process the request
        response = await call_next(request)
        
        # Add response info
        process_time = time.time() - start_time
        request_info["response_status"] = response.status_code
        request_info["processing_time_ms"] = round(process_time * 1000, 2)
        request_info["response_success"] = 200 <= response.status_code < 300
        
        # Add to queue for batch processing (non-blocking)
        try:
            request_queue.put_nowait(request_info)
        except asyncio.QueueFull:
            # Queue is full, log but don't block the request
            print("Warning: Request queue is full, dropping request info")
        
        # Also send to Elasticsearch and WebSocket in background (fire and forget)
        asyncio.create_task(send_to_elasticsearch_and_websocket(request_info))

        return response