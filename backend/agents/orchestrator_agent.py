import asyncio
import httpx
import json
import os
import sys
import time

from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import uuid4
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, EndSessionContent, TextContent, chat_protocol_spec

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import RequestBatch, OrchestratorResponse, clean_llm_output, SpecialistRequest


load_dotenv()


# Setup API keys and clients
ASI_API_KEY = os.environ.get("ASI_API_KEY")
ASI_API_URL = "https://api.asi1.ai/v1/chat/completions"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

http_client = httpx.AsyncClient()

# Setup Agent
agent = Agent(
    name="API Security Orchestrator",
    seed="API Security Orchestrator 1234455",
    port=8001,
    #endpoint=["http://localhost:8001/submit"],
    mailbox=True,
    publish_agent_details=True
)

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("[ORCHESTRATOR] Orchestrator online, ASI:One Mini client ready.")

SYSTEM_PROMPT = f"""
You are an AI Orchestrator for an API security middleware. Your job is to
classify incoming API request logs and route them to specialized analysis agents.

You will receive a list of logs in CSV format:
"ip_address,path,method,user_id,json_body_summary,times_received"
You must classify each log into one of
three categories: "auth", "search", or "general".

- "auth": Use for logs related to login, registration, or user accounts.
  (e.g., /auth/login, /api/v1/register)
- "search": Use for logs related to public data queries, product lists, or scraping.
  (e.g., /api/search, /api/products)
- "general": Use for all other logs.

Your response MUST be a single, valid JSON object with three keys:
"auth", "search", and "general". Each key must contain a list of the
full, original log objects that belong to that category. Example:
{{
    "auth": [
        "123.45.67.8,/auth/login,POST,abc123,key=value;key2=value2,1"
    ],
    "search": [
        "123.45.67.8,/api/search,GET,abc123,key=value;key2=value2,5"
    ],
    "general": [
        "123.45.67.8,/api/other,GET,abc123,key=value,13"
    ]
}}
"""

# LLM Call functions
# Groq seems to be faster, while ASI:One Mini may be more accurate for being made for agent routing.
async def asii_llm_call(csv_string: str) -> dict:
    user_prompt = f"Here are the incoming API request logs in CSV format:\n{csv_string}"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ASI_API_KEY}'
    }
    payload = {
        "model": "asi1-fast",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
    }
    
    response = await http_client.post(ASI_API_URL, headers=headers, json=payload, timeout=30.0)
    return response.json()


async def groq_llm_call(csv_string: str) -> dict:
    user_prompt = f"Here are the incoming API request logs in CSV format:\n{csv_string}"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}'
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0
    }
    
    response = await http_client.post(GROQ_API_URL, headers=headers, json=payload, timeout=30.0)
    return response.json()

# Handle a batch of requests
async def handle_batch(ctx: Context, batch: RequestBatch) -> Dict[str, List[Dict]]:
    """
    This function handles the classification and routing of a batch of requests.
    """
    ctx.logger.info(f"[ORCHESTRATOR] Received batch of {len(batch.requests)} requests. Classifying with ASI:One Mini...")

    # Minimize token usage, by compressing duplicate lines by adding count
    line_counts = {}
    for req in batch.requests:
        line = f"{req.ip_address if req.ip_address is not None else ''},{req.path},{req.method},{req.user_id if req.user_id is not None else ''},{req.json_body if req.json_body is not None else '{}'}"
        line_counts[line] = line_counts.get(line, 0) + 1
    csv_lines = [f"{line},{count}" for line, count in line_counts.items()]
    csv_string = "\n".join(csv_lines)

    # Categorize using LLM and call specialist agents
    try:
        start_time = time.time()
        response_data = await groq_llm_call(csv_string)

        llm_output_str = response_data['choices'][0]['message']['content']
        llm_output_str = clean_llm_output(llm_output_str)
        classified_logs = json.loads(llm_output_str)

        auth_logs = classified_logs.get("auth", [])
        search_logs = classified_logs.get("search", [])
        general_logs = classified_logs.get("general", [])

        end_time = time.time()
        latency = end_time - start_time
        ctx.logger.info(
            f"[ORCHESTRATOR] {len(auth_logs)} auth, {len(search_logs)} search, {len(general_logs)} general in {latency:.2f} seconds")

        # Send to specialist agents via uAgents messaging
        GENERAL_AGENT_ADDRESS = "agent1q2ackrd978swlwajsswm4kjr9cszhc9rxgnuyy7rv9jzh4v3jta25vzv668"
        AUTH_AGENT_ADDRESS = "agent1q054vfyk2qqnqwsrw804avurynvwkk9vdjcqu9q0at52zlaa5urxv0md3sk"
        SEARCH_AGENT_ADDRESS = "agent1qtpatn2rged8wspghgl8sex9e05s78fvmh84pnyf5ghn6ue0t6vkjvp03mg" 

        if auth_logs:
            try:
                specialist_msg = SpecialistRequest(logs=auth_logs)
                await ctx.send(AUTH_AGENT_ADDRESS, specialist_msg)
            except Exception as e:
                ctx.logger.error(f"[ORCHESTRATOR] ✗ Error sending to Auth agent: {e}")
        
        if search_logs:
            try:
                specialist_msg = SpecialistRequest(logs=search_logs)
                await ctx.send(SEARCH_AGENT_ADDRESS, specialist_msg)
            except Exception as e:
                ctx.logger.error(f"[ORCHESTRATOR] ✗ Error sending to Search agent: {e}")
        
        if general_logs:
            try:
                specialist_msg = SpecialistRequest(logs=general_logs)
                await ctx.send(GENERAL_AGENT_ADDRESS, specialist_msg)
            except Exception as e:
                ctx.logger.error(f"[ORCHESTRATOR] ✗ Error sending to General agent: {e}")

        return classified_logs

    except httpx.RequestError as e:
        ctx.logger.error(f"[ORCHESTRATOR] HTTP Error calling ASI:One Mini: {e}")
        return {"auth": [], "search": [], "general": []}
    except json.JSONDecodeError as e:
        ctx.logger.error(f"[ORCHESTRATOR] Error parsing JSON from ASI:One Mini: {e}")
        return {"auth": [], "search": [], "general": []}
    except Exception as e:
        ctx.logger.error(f"[ORCHESTRATOR] An unexpected error occurred: {e}")
        return {"auth": [], "search": [], "general": []}

# Set up REST API support
@agent.on_rest_post("/rest/post", RequestBatch, OrchestratorResponse)
async def handle_request_batch(ctx: Context, request: RequestBatch) -> OrchestratorResponse:
    """
    Handle the incoming request batch and return the response.
    """
    asyncio.create_task(handle_batch(ctx, request))
    return OrchestratorResponse(success=True)


# Setup Chat Protocol support
chat_protocol = Protocol(spec=chat_protocol_spec)

@chat_protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    # send the acknowledgement for receiving the message
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
 
    # collect up all the text chunks
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    try:
        # Try to parse the text as JSON to create a RequestBatch
        parsed_data = json.loads(text)
        
        # Handle different input formats
        if isinstance(parsed_data, dict):
            # Check if it has a "requests" key (wrapped format)
            if "requests" in parsed_data:
                request_batch = RequestBatch(requests=parsed_data["requests"])
            else:
                # Treat the dict as a single request and wrap it in a list
                request_batch = RequestBatch(requests=[parsed_data])
        elif isinstance(parsed_data, list):
            # Direct list of requests (unwrapped format)
            request_batch = RequestBatch(requests=parsed_data)
        else:
            response = f'Could not parse request batch. Received type: {type(parsed_data).__name__}'
            raise ValueError(response)
        
        # Fire handle_batch asynchronously in the background
        asyncio.create_task(handle_batch(ctx, request_batch))
        
        response = 'Request batch received and being processed in the background.'
    except json.JSONDecodeError as e:
        response = f'Could not parse JSON from the message: {str(e)}'
    except Exception as e:
        response = f'Could not process request batch: {str(e)}'

    # send the response back to the user
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response),
            EndSessionContent(type="end-session"),
        ]
    ))

@chat_protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass

agent.include(chat_protocol, publish_manifest=True)


# Handle specialist agent responses
@agent.on_message(model=OrchestratorResponse)
async def handle_specialist_response(ctx: Context, sender: str, response: OrchestratorResponse):
    """
    Handle acknowledgment responses from specialist agents.
    """
    ctx.logger.info(f"[ORCHESTRATOR] ✓ Received acknowledgment from {sender[:16]}... (success={response.success})")


if __name__ == "__main__":
    agent.run()