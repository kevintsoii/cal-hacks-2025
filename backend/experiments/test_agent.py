#!/usr/bin/env python3
"""
Simple script to test the agent system by sending a batch of requests
"""
import asyncio
import httpx
from agents.models import APIRequestLog, RequestBatch
from uagents import Agent


async def send_test_requests():
    """Send multiple requests to trigger the agent pipeline"""
    async with httpx.AsyncClient() as client:
        # Send 20 failed login attempts from different IPs
        print("Sending 20 failed login attempts...")
        for i in range(20):
            try:
                response = await client.post(
                    "http://localhost:8000/login",
                    json={"username": "admin", "password": f"wrong{i}"},
                    headers={"mock-ip": f"192.168.1.{i % 5}"},
                    timeout=5.0
                )
                print(f"Request {i+1}: {response.status_code}")
            except Exception as e:
                print(f"Request {i+1} failed: {e}")

            await asyncio.sleep(0.1)  # Small delay between requests

        print("\nWaiting 5 seconds for agent processing...")
        await asyncio.sleep(5)

        print("\nSending 10 search requests...")
        for i in range(10):
            try:
                response = await client.post(
                    "http://localhost:8000/search",
                    json={
                        "usernames": [f"user{i}", f"user{i+1}", f"user{i+2}"]
                    },
                    headers={"mock-ip": f"10.0.0.{i % 3}"},
                    timeout=5.0
                )
                print(f"Search request {i+1}: {response.status_code}")
            except Exception as e:
                print(f"Search request {i+1} failed: {e}")

            await asyncio.sleep(0.2)

        print("\n✅ Test completed! Check your agent logs for processing details.")


async def test_direct_agent_message():
    """
    Test sending a message directly to the orchestrator agent
    (This demonstrates how the middleware sends batches to the orchestrator)
    """
    from uagents import Bureau

    # Create sample request logs
    sample_requests = [
        APIRequestLog(
            ip_address="192.168.1.1",
            path="/login",
            method="POST",
            user_id=None
        ),
        APIRequestLog(
            ip_address="192.168.1.2",
            path="/login",
            method="POST",
            user_id=None
        ),
        APIRequestLog(
            ip_address="10.0.0.1",
            path="/search",
            method="POST",
            user_id="user123"
        ),
    ]

    # Create a test agent to send messages
    test_agent = Agent(name="test_sender", seed="test_seed_123")

    @test_agent.on_event("startup")
    async def send_batch(ctx):
        print("Sending batch to orchestrator...")
        # You would send to the orchestrator's address here
        # This requires knowing the orchestrator's address
        ctx.logger.info("Test agent ready to send messages")

    print("Direct agent message test - requires orchestrator address")

if __name__ == "__main__":
    print("=" * 60)
    print("Agent System Test")
    print("=" * 60)
    print("\nMake sure the following are running:")
    print("1. Redis")
    print("2. Elasticsearch")
    print("3. Orchestrator Agent (python agents/orchestrator_agent.py)")
    print("4. Auth Agent (python agents/auth_agent.py)")
    print("5. FastAPI Server (python main.py)")
    print("=" * 60)

    choice = input(
        "\nChoose test:\n1. HTTP requests (simpler)\n2. Direct agent message\nEnter 1 or 2: ")

    if choice == "1":
        asyncio.run(send_test_requests())
    elif choice == "2":
        asyncio.run(test_direct_agent_message())
    else:
        print("Invalid choice")