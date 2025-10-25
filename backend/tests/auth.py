"""Authentication endpoint tests (brute force, credential stuffing, etc.)"""
from fastapi import WebSocket
from tests.config import RequestConfig, generate_random_ip
import asyncio


async def run_admin_100_test(websocket: WebSocket, cancellation_event: asyncio.Event, execute_test_requests):
    """
    Brute force attack test: Login to "admin" 100x with different IPs.
    Generates request configurations and executes them.
    """
    requests = []
    
    for i in range(100):
        fake_ip = generate_random_ip()
        request = RequestConfig(
            url="http://localhost:8000/login",
            method="POST",
            json_body={
                "username": "admin",
                "password": "wrongpassword"  # Intentionally wrong for brute force
            },
            headers={
                "mock-ip": fake_ip
            },
            timeout=10.0
        )
        requests.append(request)
    
    # Execute all requests using the generic function
    await execute_test_requests(websocket, requests, cancellation_event, max_concurrent=2, delay_between_requests=0.25)


async def run_admin_1000_test(websocket: WebSocket, cancellation_event: asyncio.Event, execute_test_requests):
    """
    Large brute force attack test: Login to "admin" 1000x with different IPs.
    """
    requests = []
    
    for i in range(1000):
        fake_ip = generate_random_ip()
        request = RequestConfig(
            url="http://localhost:8000/login",
            method="POST",
            json_body={
                "username": "admin",
                "password": "wrongpassword"
            },
            headers={
                "mock-ip": fake_ip
            },
            timeout=10.0
        )
        requests.append(request)
    
    await execute_test_requests(websocket, requests, cancellation_event, max_concurrent=5, delay_between_requests=0.1)


async def run_credential_stuffing_test(websocket: WebSocket, cancellation_event: asyncio.Event, execute_test_requests):
    """
    Credential stuffing attack: Try 100 different username/password combinations.
    """
    requests = []
    
    # Generate 100 different credential pairs
    usernames = [f"user{i}" for i in range(100)]
    
    for username in usernames:
        fake_ip = generate_random_ip()
        request = RequestConfig(
            url="http://localhost:8000/login",
            method="POST",
            json_body={
                "username": username,
                "password": "CommonPassword123"  # Using common password for credential stuffing
            },
            headers={
                "mock-ip": fake_ip
            },
            timeout=10.0
        )
        requests.append(request)
    
    await execute_test_requests(websocket, requests, cancellation_event, max_concurrent=3, delay_between_requests=0.2)