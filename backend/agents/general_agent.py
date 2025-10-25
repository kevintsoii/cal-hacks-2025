import time
from models import (
    APIRequestLog, RequestBatch, OrchestratorResponse, clean_llm_output, SpecialistRequest
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



# SETUP
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


agent = Agent(
    name="General API Specialist",
    seed="General API Specialist 122343290",
    port=8004,
    #endpoint=["http://localhost:8004/submit"],
    mailbox=True,
    publish_agent_details=True
)

chat_protocol = Protocol(spec=chat_protocol_spec)

# Create a persistent async client for the agent
http_client = httpx.AsyncClient()





# 2. DEFINE THE PROMPT
SYSTEM_PROMPT = f"""
You are an API security specialist, specialization in general API requests.
"""




# MAIN
async def handle_batch(ctx: Context, logs: SpecialistRequest) -> Dict[str, List[Dict]]:
    """
    This function handles the classification and routing of a batch of requests.
    """
    ctx.logger.info(f"[GENERAL] Received batch of {len(logs.logs)}")

    try:
        start_time = time.time()

        llm_output_str = "call groq here"

        # Clean the LLM output string to remove markdown code blocks
        llm_output_str = clean_llm_output(llm_output_str)

        # 4. Parse the LLM's JSON response
        mitigations = json.loads(llm_output_str)


        end_time = time.time()
        latency = end_time - start_time
        ctx.logger.info(f"[GENERAL] Mitigations: {len(mitigations)} in {latency} seconds")

        later = "apply calibration agent"

        return mitigations

    except httpx.RequestError as e:
        ctx.logger.error(f"[GENERAL] HTTP Error calling Groq: {e}")
        return []
    except json.JSONDecodeError as e:
        ctx.logger.error(
            f"[GENERAL] Error parsing JSON from Groq: {e}. Response was: {llm_output_str}")
        return []
    except Exception as e:
        ctx.logger.error(f"[GENERAL] An unexpected error occurred: {e}")
        return []



@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("[GENERAL] Online, Groq client ready.")


@agent.on_message(model=SpecialistRequest)
async def handle_request_batch(ctx: Context, sender: str, request: SpecialistRequest) -> OrchestratorResponse:
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
            request_batch = SpecialistRequest(logs=parsed_data.get("logs", []))
            
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