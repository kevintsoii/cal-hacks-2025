import time
from models import (
    APIRequestLog, RequestBatch, OrchestratorResponse, clean_llm_output
)
import os
import json
import httpx  # For making async API calls
import asyncio
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from typing import List, Dict

from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

# Use a relative import ('.')

# 1. SETUP AGENT AND ASI:ONE CLIENT
ASI_API_KEY = os.environ.get("ASI_API_KEY")
ASI_API_URL = "https://api.asi1.ai/v1/chat/completions"


agent = Agent(
    name="API Security Orchestrator",
    seed="API Security Orchestrator 1234455",
    port=8001,
    #endpoint=["http://localhost:8001/submit"],
    mailbox=True,
    publish_agent_details=True
)

chat_protocol = Protocol(spec=chat_protocol_spec)

# Create a persistent async client for the agent
http_client = httpx.AsyncClient()





# 2. DEFINE THE ORCHESTRATOR'S PROMPT
SYSTEM_PROMPT = f"""
You are an AI Orchestrator for an API security middleware. Your job is to
classify incoming API request logs and route them to specialized analysis agents.

You will receive a list of logs in CSV format:
"ip_address,path,method,user_id,json_body"
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
        "123.45.67.8,/auth/login,POST,abc123,{{}}"
    ],
    "search": [
        "123.45.67.8,/api/search,GET,abc123,{{}}"
    ],
    "general": [
        "123.45.67.8,/api/other,GET,abc123,{{}}"
    ]
}}
"""

async def handle_batch(ctx: Context, batch: RequestBatch) -> Dict[str, List[Dict]]:
    """
    This function handles the classification and routing of a batch of requests.
    """
    ctx.logger.info(f"Received batch of {len(batch.requests)} requests. Classifying with ASI:One Mini...")

    # 1. Serialize logs for the prompt
    # Manually serialize batch as CSV string: header then comma-separated fields per line, no libraries
    csv_lines = []
    for req in batch.requests:
        line = f"{req.ip_address if req.ip_address is not None else ''},{req.path},{req.method},{req.user_id if req.user_id is not None else ''},{req.json_body if req.json_body is not None else '{}'}"
        csv_lines.append(line)
    csv_string = "\n".join(csv_lines)
    user_prompt = f"Here are the incoming API request logs in CSV format:\n{csv_string}"

    # 2. Prepare the ASI:One API request
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
        "response_format": {"type": "json_object"},  # Request JSON output
    }

    # 3. Call ASI:One Mini
    try:
        start_time = time.time()
        response = await http_client.post(ASI_API_URL, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()  # Raise an error for bad responses

        response_data = response.json()
        llm_output_str = response_data['choices'][0]['message']['content']

        # Clean the LLM output string to remove markdown code blocks
        llm_output_str = clean_llm_output(llm_output_str)

        # 4. Parse the LLM's JSON response
        classified_logs = json.loads(llm_output_str)

        auth_logs = classified_logs.get("auth", [])
        search_logs = classified_logs.get("search", [])
        general_logs = classified_logs.get("general", [])

        end_time = time.time()
        latency = end_time - start_time
        ctx.logger.info(
            f"ASI:One Mini classified: {len(auth_logs)} auth, {len(search_logs)} search, {len(general_logs)} general in {latency} seconds")
        

        # 5. Broadcast tasks to specialists
        tasks_to_run = []
        # if auth_logs:
        #     # Re-serialize from dicts back into Model objects
        #     tasks = [APIRequestLog(**log) for log in auth_logs]
        #     tasks_to_run.append(
        #         ctx.broadcast(auth_protocol.digest, RequestBatch(requests=tasks))
        #     )

        # if search_logs:
        #     tasks = [APIRequestLog(**log) for log in search_logs]
        #     tasks_to_run.append(
        #         ctx.broadcast(search_protocol.digest,
        #                       RequestBatch(requests=tasks))
        #     )

        # if general_logs:
        #     tasks = [APIRequestLog(**log) for log in general_logs]
        #     tasks_to_run.append(
        #         ctx.broadcast(general_protocol.digest,
        #                       RequestBatch(requests=tasks))
        #     )

        if tasks_to_run:
            await asyncio.gather(*tasks_to_run)
            ctx.logger.info("All specialized tasks have been broadcasted.")

        return classified_logs

    except httpx.RequestError as e:
        ctx.logger.error(f"HTTP Error calling ASI:One Mini: {e}")
        return {"auth": [], "search": [], "general": []}
    except json.JSONDecodeError as e:
        ctx.logger.error(
            f"Error parsing JSON from ASI:One Mini: {e}. Response was: {llm_output_str}")
        return {"auth": [], "search": [], "general": []}
    except Exception as e:
        ctx.logger.error(f"An unexpected error occurred: {e}")
        return {"auth": [], "search": [], "general": []}



@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Orchestrator online, ASI:One Mini client ready.")


@agent.on_rest_post("/rest/post", RequestBatch, OrchestratorResponse)
async def handle_request_batch(ctx: Context, request: RequestBatch) -> OrchestratorResponse:
    """
    Handle the incoming request batch and return the response.
    """
    asyncio.create_task(handle_batch(ctx, request))
    return OrchestratorResponse(success=True)

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
        
        # Validate that it has the expected structure
        if isinstance(parsed_data, dict):
            request_batch = RequestBatch(requests=parsed_data)
            
            # Fire handle_batch asynchronously in the background
            asyncio.create_task(handle_batch(ctx, request_batch))
            
            response = 'Request batch received and being processed in the background.'
        else:
            response = f'Could not parse request batch. Expected format: [{{}}]'
    except json.JSONDecodeError:
        response = 'Could not parse JSON from the message.'
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

if __name__ == "__main__":
    agent.run()