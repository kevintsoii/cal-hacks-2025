"""Search endpoint tests (scraping, injection attacks, etc.)"""
from fastapi import WebSocket
from tests.config import RequestConfig, generate_random_ip
import asyncio


async def run_admin_search_test(websocket: WebSocket, cancellation_event: asyncio.Event, execute_test_requests):
    """
    Admin search abuse: Search for "admin" 200 times rapidly.
    """
    requests = []
    
    for i in range(200):
        fake_ip = generate_random_ip()
        request = RequestConfig(
            url="http://localhost:8000/search",
            method="POST",
            json_body={
                "yourUsername": "admin",
                "usernames": ["admin"]
            },
            headers={
                "mock-ip": fake_ip
            },
            timeout=10.0
        )
        requests.append(request)
    
    await execute_test_requests(websocket, requests, cancellation_event, max_concurrent=5, delay_between_requests=0.1)


async def run_scraping_pattern_test(websocket: WebSocket, cancellation_event: asyncio.Event, execute_test_requests):
    """
    Scraping pattern: Sequential user ID searches from 1-1000.
    """
    requests = []
    
    # Use same IP to simulate scraping behavior
    scraper_ip = generate_random_ip()
    
    for user_id in range(1, 1001):
        request = RequestConfig(
            url="http://localhost:8000/search",
            method="POST",
            json_body={
                "usernames": [f"user{user_id}"]
            },
            headers={
                "mock-ip": scraper_ip
            },
            timeout=10.0
        )
        requests.append(request)
    
    await execute_test_requests(websocket, requests, cancellation_event, max_concurrent=10, delay_between_requests=0.05)


async def run_sql_injection_test(websocket: WebSocket, cancellation_event: asyncio.Event, execute_test_requests):
    """
    SQL injection attempts: 50 requests with various SQL injection payloads.
    """
    requests = []
    
    # Common SQL injection payloads
    sql_payloads = [
        "' OR '1'='1",
        "admin' --",
        "' OR 1=1--",
        "admin' OR '1'='1",
        "' UNION SELECT NULL--",
        "1' ORDER BY 1--",
        "' DROP TABLE users--",
        "admin'; DROP TABLE users--",
        "1' AND '1'='1",
        "' OR 'a'='a"
    ]
    
    for i in range(50):
        fake_ip = generate_random_ip()
        payload = sql_payloads[i % len(sql_payloads)]
        
        request = RequestConfig(
            url="http://localhost:8000/search",
            method="POST",
            json_body={
                "usernames": [payload]
            },
            headers={
                "mock-ip": fake_ip
            },
            timeout=10.0
        )
        requests.append(request)
    
    await execute_test_requests(websocket, requests, cancellation_event, max_concurrent=3, delay_between_requests=0.2)