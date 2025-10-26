import time
import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    APIRequestLog, RequestBatch, OrchestratorResponse, clean_llm_output, SpecialistRequest,
    Mitigation, MitigationBatch
)
from utils.rule_loader import load_agent_rules
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

CALIBRATION_AGENT_ADDRESS = "agent1qgnl0fly845g2zlx904lsgwygl4vl7jygcx7xyxf82zu95g26mgmy0dk9rt"


agent = Agent(
    name="Search API Specialist",
    seed="Search API Specialist Agent 234243242342",
    port=8003,
    #endpoint=["http://localhost:8003/submit"],
    mailbox=True,
    publish_agent_details=True
)

chat_protocol = Protocol(spec=chat_protocol_spec)

# Create a persistent async client for the agent
http_client = httpx.AsyncClient()





# 2. DEFINE THE SEARCH-SPECIFIC PROMPT
SEARCH_SPECIALIST_PROMPT = """You are an AI security specialist focused on SEARCH and QUERY endpoints (/search, /query, /api/products, /api/users, data retrieval APIs, etc.).

Your responsibilities:
1. Review the provided search/query API activity logs for suspicious patterns
2. Detect search-specific threats such as:
   - Web scraping (high-volume automated data extraction)
   - Data exfiltration (bulk data access patterns)
   - API abuse (excessive query rates)
   - Enumeration attacks (systematic ID/username probing)
   - Reconnaissance (mapping available data/endpoints)
   - Bot activity (non-human search patterns)
   - Content scraping (downloading large amounts of public data)
   - Competitive intelligence gathering
3. Recommend targeted mitigations in JSON format

Input format: CSV logs with format "ip,path,method,user_id,body,count"
For search endpoints, the body often contains query parameters, search terms, filters, or pagination data.

Optional additional context:
- You have access to a single callable tool:
  {
    "name": "fetch_from_elasticsearch",
    "description": "Query historical search/query logs from Elasticsearch to find scraping patterns, excessive query volumes, or systematic data extraction from the same source.",
    "parameters": {
      "type": "object",
      "properties": {
        "query_string": { "type": "string", "description": "Natural language query like 'find search requests from IP 10.0.0.50 in last hour' or 'show high-volume queries from user scraper123'" }
      },
      "required": ["query_string"]
    }
  }

If you believe additional context is required (e.g., historical query volume, search patterns, systematic access), you may call "fetch_from_elasticsearch" with a specific query.

Output format - Return ONLY a valid JSON array of mitigation objects:
[
  {
    "entity_type": "ip" or "user",
    "entity": "<ip_address or username>",
    "severity": "low|medium|high|critical",
    "mitigation": "delay|captcha|temp_block|ban",
    "reason": "brief explanation of why this mitigation is needed (e.g., '500 search requests in 10 minutes - scraping detected')"
  }
]

Examples of search threats to detect:
- 100+ search requests in short time → "web scraping / data exfiltration"
- Systematic ID enumeration (1,2,3,4...) → "enumeration attack"
- Same query repeated many times → "bot / automated scraping"
- Rapid pagination through all results → "bulk data download"
- Unusual user-agent + high volume → "scraper bot detected"

If no threats detected, return an empty array: []
Do NOT include any text outside the JSON array in your final response.
"""

# Elasticsearch tool definition
ES_TOOL = {
    "type": "function",
    "function": {
        "name": "fetch_from_elasticsearch",
        "description": "Query search/query logs from Elasticsearch to find scraping patterns, excessive query volumes, or systematic data extraction",
        "parameters": {
            "type": "object",
            "properties": {
                "query_string": {
                    "type": "string",
                    "description": "Natural language query to search for search-related logs (e.g., 'find search requests from IP 10.0.0.50 in last hour')"
                }
            },
            "required": ["query_string"]
        }
    }
}


async def fetch_from_elasticsearch(ctx: Context, query_string: str) -> Dict:
    """
    Query Elasticsearch for search/query logs matching the query string.
    Focuses on search endpoints: /search, /query, /api/products, /api/users, etc.
    """
    try:
        from db.elasticsearch import elasticsearch_client
        
        ctx.logger.info(f"[SEARCH] 🔍 Elasticsearch query: {query_string}")
        
        query_lower = query_string.lower()
        
        # Build ES query
        es_query = {
            "bool": {
                "must": [],
                "filter": []
            }
        }
        
        # Extract IP if present
        import re
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, query_string)
        if ips:
            # Use .keyword for exact string matching in Elasticsearch
            es_query["bool"]["must"].append({"terms": {"client_ip.keyword": ips}})
            ctx.logger.info(f"[SEARCH]   🔍 Filtering by IPs: {ips}")
        
        # Extract username if present
        if "user" in query_lower or "username" in query_lower:
            user_match = re.search(r'user(?:name)?\s+["\']?(\w+)["\']?', query_lower)
            if user_match:
                username = user_match.group(1)
                # Use .keyword for exact string matching
                es_query["bool"]["must"].append({"term": {"user.keyword": username}})
                ctx.logger.info(f"[SEARCH]   🔍 Filtering by user: {username}")
        
        # Filter for search/query endpoints - use wildcard for flexible matching
        search_paths = ["/search", "/query", "/api/products", "/api/users", "/api/items", "/find", "/lookup"]
        es_query["bool"]["should"] = [
            {"wildcard": {"path.keyword": f"*{path}*"}} for path in search_paths
        ]
        es_query["bool"]["minimum_should_match"] = 1
        ctx.logger.info(f"[SEARCH]   🔍 Filtering for search endpoints: {search_paths}")
        
        # Extract time range (default 1 hour for search - longer than auth)
        time_value = 1
        time_unit = 'h'
        
        if "last" in query_lower:
            time_match = re.search(r'last (\d+)\s*(minute|min|hour|hr)?s?', query_lower)
            if time_match:
                time_value = int(time_match.group(1))
                unit = time_match.group(2)
                if unit and unit.startswith('m'):
                    time_unit = 'm'
                elif unit and unit.startswith('h'):
                    time_unit = 'h'
        
        time_filter = {
            "range": {
                "timestamp": {
                    "gte": f"now-{time_value}{time_unit}",
                    "lte": "now"
                }
            }
        }
        es_query["bool"]["filter"].append(time_filter)
        
        # Debug logging - show the actual query
        ctx.logger.info(f"[SEARCH] 🔍 Executing Elasticsearch query:")
        ctx.logger.info(f"[SEARCH]    Index: api_requests")
        ctx.logger.info(f"[SEARCH]    Time range: last {time_value}{time_unit}")
        ctx.logger.info(f"[SEARCH]    Query: {json.dumps(es_query, indent=2)}")
        
        # Execute search
        results = await elasticsearch_client.search(
            index_name="api_requests",
            query=es_query,
            size=100  # Allow more results for search (scraping can be high volume)
        )
        
        ctx.logger.info(f"[SEARCH] ✓ Found {len(results)} search logs from Elasticsearch")
        
        # Format results as CSV logs
        additional_logs = []
        for doc in results:
            client_ip = doc.get('client_ip', 'unknown')
            path = doc.get('path', '/')
            method = doc.get('method', 'GET')
            user = doc.get('user', '')
            body_json = doc.get('body_json', {})
            body_str = json.dumps(body_json) if body_json else ''
            
            # Create CSV format log entry
            log_str = f"{client_ip},{path},{method},{user},{body_str},1"
            additional_logs.append(log_str)
        
        if additional_logs:
            ctx.logger.info(f"[SEARCH]   Sample log: {additional_logs[0][:100]}...")
        
        return {
            "success": True,
            "logs": additional_logs,
            "count": len(additional_logs),
            "query": query_string,
            "es_query": es_query
        }
        
    except Exception as e:
        ctx.logger.error(f"[SEARCH] ✗ Elasticsearch query failed: {e}")
        import traceback
        ctx.logger.error(f"[SEARCH] ✗ Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "logs": [],
            "count": 0,
            "error": str(e)
        }


# MAIN
async def handle_batch(ctx: Context, logs: SpecialistRequest, return_metadata: bool = False):
    """
    This function handles search/query requests and analyzes them for scraping and abuse.
    """
    ctx.logger.info(f"[SEARCH] ✓ Processing batch of {len(logs.logs)} search logs")
    
    try:
        start_time = time.time()
        
        # Log first few entries
        for i, log in enumerate(logs.logs[:3]):
            ctx.logger.info(f"[SEARCH]   Log {i+1}: {log[:80]}{'...' if len(log) > 80 else ''}")
        
        if len(logs.logs) > 3:
            ctx.logger.info(f"[SEARCH]   ... and {len(logs.logs) - 3} more logs")
        
        # Prepare logs for Groq analysis
        original_logs = logs.logs.copy()
        logs_text = "\n".join(logs.logs)
        user_prompt = f"Analyze these search/query API request logs for security threats (scraping, abuse, enumeration):\n\n{logs_text}"
        
        # Track extended batch info
        additional_logs_from_es = []
        es_query_used = None
        
        # Call Groq for threat analysis (with tool calling support)
        ctx.logger.info(f"[SEARCH] Calling Groq for search threat analysis with tool support...")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GROQ_API_KEY}'
        }
        
        # Load custom rules and append to system prompt
        custom_rules = load_agent_rules("search")
        system_prompt = SEARCH_SPECIALIST_PROMPT + custom_rules
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0,
            "tools": [ES_TOOL],
            "tool_choice": "auto"
        }
        
        response = await http_client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            ctx.logger.error(f"[SEARCH] Groq API error {response.status_code}: {response.text}")
            return []
        
        result = response.json()
        assistant_message = result['choices'][0]['message']
        
        # Check if LLM wants to use the ES tool
        if assistant_message.get('tool_calls'):
            ctx.logger.info(f"[SEARCH] 🔧 LLM requested tool call for historical search data")
            
            tool_call = assistant_message['tool_calls'][0]
            function_name = tool_call['function']['name']
            function_args = json.loads(tool_call['function']['arguments'])
            
            if function_name == "fetch_from_elasticsearch":
                query_string = function_args.get('query_string', '')
                es_query_used = query_string
                
                # Execute the tool
                es_result = await fetch_from_elasticsearch(ctx, query_string)
                additional_logs_from_es = es_result.get('logs', [])
                
                # Add the tool response to messages and make a second call
                messages.append(assistant_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "name": function_name,
                    "content": json.dumps(es_result)
                })
                
                # Extend the original batch with ES logs
                extended_logs = original_logs + additional_logs_from_es
                extended_logs_text = "\n".join(extended_logs)
                
                ctx.logger.info(f"[SEARCH] 📊 Extended batch: {len(original_logs)} original + {len(additional_logs_from_es)} from ES = {len(extended_logs)} total")
                
                # Update the user message with extended logs
                messages.append({
                    "role": "user",
                    "content": f"Now analyze the complete search dataset including the additional logs:\n\n{extended_logs_text}"
                })
                
                # Make second call with extended context
                payload["messages"] = messages
                payload.pop("tools", None)
                payload.pop("tool_choice", None)
                payload["response_format"] = {"type": "json_object"}
                
                response = await http_client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    ctx.logger.error(f"[SEARCH] Groq API error on second call {response.status_code}: {response.text}")
                    return []
                
                result = response.json()
        
        llm_output_str = result['choices'][0]['message']['content']
        
        # Clean and parse the LLM output
        llm_output_str = clean_llm_output(llm_output_str)
        
        # Parse mitigations
        try:
            parsed = json.loads(llm_output_str)
            if isinstance(parsed, list):
                mitigations = parsed
            elif isinstance(parsed, dict) and "mitigations" in parsed:
                mitigations = parsed["mitigations"]
            elif isinstance(parsed, dict):
                mitigations = []
            else:
                mitigations = []
        except json.JSONDecodeError as e:
            ctx.logger.error(f"[SEARCH] Failed to parse Groq response: {e}")
            ctx.logger.error(f"[SEARCH] Response was: {llm_output_str[:200]}")
            mitigations = []
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Log batch extension info
        if additional_logs_from_es:
            ctx.logger.info(f"[SEARCH] 📊 Batch Extended: {len(original_logs)} original + {len(additional_logs_from_es)} from ES")
            ctx.logger.info(f"[SEARCH] 🔍 ES Query: {es_query_used}")
        
        ctx.logger.info(f"[SEARCH] ✓ Analysis complete: {len(mitigations)} mitigations in {latency:.3f}s")
        
        # Log detected threats
        if mitigations:
            for i, m in enumerate(mitigations[:5], 1):
                ctx.logger.info(
                    f"[SEARCH]   Threat {i}: {m.get('entity_type')} {m.get('entity')} "
                    f"-> {m.get('mitigation')} (severity: {m.get('severity')})"
                )
            if len(mitigations) > 5:
                ctx.logger.info(f"[SEARCH]   ... and {len(mitigations) - 5} more threats")
        else:
            ctx.logger.info(f"[SEARCH]   No search threats detected")
        
        # Return mitigations or full metadata
        if return_metadata:
            return {
                "mitigations": mitigations,
                "original_batch_size": len(original_logs),
                "additional_logs_from_es": additional_logs_from_es,
                "es_query_used": es_query_used,
                "extended_batch_size": len(original_logs) + len(additional_logs_from_es),
                "tool_called": len(additional_logs_from_es) > 0,
                "latency": latency
            }
        else:
            return mitigations

    except httpx.RequestError as e:
        ctx.logger.error(f"[SEARCH] ✗ HTTP error calling Groq: {e}")
        if return_metadata:
            return {"mitigations": [], "error": str(e)}
        return []
    except Exception as e:
        ctx.logger.error(f"[SEARCH] ✗ An unexpected error occurred: {e}")
        if return_metadata:
            return {"mitigations": [], "error": str(e)}
        return []



@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("[SEARCH] Online, Groq client ready.")


@agent.on_message(model=SpecialistRequest)
async def handle_request_batch(ctx: Context, sender: str, request: SpecialistRequest):
    """
    Handle the incoming request batch from orchestrator agent.
    """
    ctx.logger.info(f"[SEARCH] ✓ Received message from {sender[:16]}...")
    
    # Process the batch and get mitigations
    mitigations_list = await handle_batch(ctx, request)
    
    # Send acknowledgment back to orchestrator
    await ctx.send(sender, OrchestratorResponse(success=True))
    
    # If mitigations were detected, send them to Calibration Agent
    if mitigations_list and len(mitigations_list) > 0:
        try:
            # Convert dict mitigations to Mitigation models
            mitigation_models = []
            for m in mitigations_list:
                mitigation_models.append(Mitigation(
                    entity_type=m.get("entity_type", "ip"),
                    entity=m.get("entity", "unknown"),
                    severity=m.get("severity", "low"),
                    mitigation=m.get("mitigation", "delay"),
                    reason=m.get("reason", ""),
                    source_agent="search"
                ))
            
            # Create batch and send to Calibration Agent
            mitigation_batch = MitigationBatch(
                mitigations=mitigation_models,
                source_agent="search"
            )
            
            ctx.logger.info(f"[SEARCH] Sending {len(mitigation_models)} mitigations to Calibration Agent...")
            await ctx.send(CALIBRATION_AGENT_ADDRESS, mitigation_batch)
            ctx.logger.info(f"[SEARCH] ✓ Mitigations sent to Calibration Agent")
            
        except Exception as e:
            ctx.logger.error(f"[SEARCH] ✗ Error sending to Calibration Agent: {e}")

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