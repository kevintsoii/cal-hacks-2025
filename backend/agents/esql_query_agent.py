"""
Elasticsearch Query Agent for Fetch.ai
Generates ESQL queries dynamically from natural language input.
Compatible with Fetch.ai Agentverse and follows orchestrator agent structure.
"""

import time
import os
import json
import httpx
import asyncio
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model
from typing import Dict, Any, List, Optional
from elasticsearch import AsyncElasticsearch

from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

# ============================================================================
# 1. AGENT SETUP
# ============================================================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Elasticsearch configuration
ELASTICSEARCH_ENDPOINT = os.environ.get("ELASTICSEARCH_ENDPOINT")
ELASTICSEARCH_API_KEY = os.environ.get("ELASTICSEARCH_API_KEY")

agent = Agent(
    name="Elasticsearch Query Generator",
    seed="elasticsearch_query_agent_seed_98765",
    port=8006,  # ESQL Query Agent on dedicated port
    mailbox=True,
    readme_path="README.md",
    publish_agent_details=True
)

chat_protocol = Protocol(spec=chat_protocol_spec)

# Create persistent HTTP client
http_client = httpx.AsyncClient()

# Create Elasticsearch client
elasticsearch_client = None
if ELASTICSEARCH_ENDPOINT and ELASTICSEARCH_API_KEY:
    elasticsearch_client = AsyncElasticsearch(
        ELASTICSEARCH_ENDPOINT,
        api_key=ELASTICSEARCH_API_KEY,
        verify_certs=True,
        request_timeout=30
    )


# ============================================================================
# 2. SYSTEM PROMPT FOR ESQL QUERY GENERATION
# ============================================================================

SYSTEM_PROMPT = """
You are an expert Elasticsearch Query Generator. Your job is to convert natural language 
requests into valid ESQL queries for the Elasticsearch api_requests index.

COMPLETE FIELD SCHEMA FOR api_requests INDEX:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST METADATA:
- timestamp (datetime) - when request occurred
- method (keyword) - HTTP method: GET, POST, PUT, DELETE, PATCH, etc.
- path (text/keyword) - API endpoint path (e.g., /login, /api/users)
- full_url (text) - complete URL with protocol and host
- processing_time_ms (float) - request processing duration in milliseconds

CLIENT INFORMATION:
- client_ip (ip/keyword) - source IP address
- client_port (integer) - source port number
- origin (keyword) - CORS origin header
- referer (text) - HTTP referer header
- user_agent (text/keyword) - browser/client user agent string

AUTHENTICATION & USER:
- user (text/keyword) - authenticated username (extracted from request)
- body_json.username (keyword) - username from JSON body (login attempts)
- body_json.password (keyword) - HASHED password from JSON body (DO NOT use raw passwords!)

REQUEST BODY:
- body_raw (text) - raw request body as string
- body_size (integer) - size of request body in bytes
- body_json.* (nested fields) - any JSON field from request body
- content_type (keyword) - Content-Type header

RESPONSE:
- response_status (integer) - HTTP status code (200, 401, 403, 404, 500, etc.)
- response_success (boolean) - true if 2xx/3xx, false if 4xx/5xx

HEADERS:
- accept (keyword) - Accept header value

INTERNAL:
- _id (keyword) - Elasticsearch document ID
- _index (keyword) - index name (always "api_requests")
- _score (float) - relevance score

COMMON FIELD ALIASES (understand these as the same):
- "username" → body_json.username OR user
- "ip" / "ip address" → client_ip
- "status code" / "response code" → response_status
- "failed" / "error" → response_success == false OR response_status >= 400
- "successful" / "success" → response_success == true OR response_status < 400
- "slow" / "performance" → processing_time_ms > threshold

ESQL SYNTAX RULES:
1. Always start with: FROM api_requests
2. Use WHERE for filtering
3. Use STATS for aggregations
4. Use SORT for ordering
5. Use LIMIT for result count
6. Time ranges: timestamp >= NOW() - 1 hour
7. String matching: field == "value" OR field LIKE "pattern*"
8. Numeric ranges: field >= 100 AND field <= 1000

EXAMPLE QUERIES:

1. Natural: "Show failed logins"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 24 hours
     AND path == "/login"
     AND response_status == 401
   | LIMIT 100

2. Natural: "Find IPs with more than 10 failed attempts"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 24 hours
     AND response_success == false
   | STATS count = COUNT(*) BY client_ip
   | WHERE count > 10
   | SORT count DESC

3. Natural: "Show slow requests over 1 second"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 1 hour
     AND processing_time_ms >= 1000
   | SORT processing_time_ms DESC
   | LIMIT 50

4. Natural: "Get all activity for username admin"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 24 hours
     AND (user == "admin" OR body_json.username == "admin")
   | LIMIT 100

5. Natural: "Show all POST requests from username john"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 1 hour
     AND method == "POST"
     AND (user == "john" OR body_json.username == "john")
   | LIMIT 100

6. Natural: "Find failed login attempts for username admin"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 1 hour
     AND path == "/login"
     AND body_json.username == "admin"
     AND response_status == 401
   | LIMIT 100

7. Natural: "Show requests from IP 192.168.1.100"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 1 hour
     AND client_ip == "192.168.1.100"
   | LIMIT 100

8. Natural: "Get all 500 errors in the last 6 hours"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 6 hours
     AND response_status >= 500
   | SORT timestamp DESC
   | LIMIT 100

9. Natural: "Show user agents accessing /api/admin"
   ESQL:
   FROM api_requests
   | WHERE timestamp >= NOW() - 1 hour
     AND path LIKE "/api/admin*"
   | STATS count = COUNT(*) BY user_agent
   | SORT count DESC

10. Natural: "Find all requests with body size over 1KB"
    ESQL:
    FROM api_requests
    | WHERE timestamp >= NOW() - 1 hour
      AND body_size > 1024
    | SORT body_size DESC
    | LIMIT 100

11. Natural: "Show me a pie chart of endpoint paths"
    ESQL:
    FROM api_requests
    | WHERE timestamp >= NOW() - 24 hours
    | STATS count = COUNT(*) BY path
    | SORT count DESC

12. Natural: "Show distribution of HTTP methods"
    ESQL:
    FROM api_requests
    | WHERE timestamp >= NOW() - 24 hours
    | STATS count = COUNT(*) BY method
    | SORT count DESC

13. Natural: "Show me IPs in the last hour" (explicit time)
    ESQL:
    FROM api_requests
    | WHERE timestamp >= NOW() - 1 hour
    | STATS count = COUNT(*) BY client_ip
    | SORT count DESC

YOUR RESPONSE MUST BE VALID JSON:
{
    "natural_language": "the user's original request",
    "esql_query": "the generated ESQL query",
    "explanation": "brief explanation of what the query does",
    "estimated_results": "high/medium/low estimate of result count"
}

QUERY GENERATION GUIDELINES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TIME DEFAULTS:
   - No time specified → last 24 hours (NOW() - 24 hours)
   - "recent" / "latest" → last 24 hours
   - "last hour" / "past hour" → NOW() - 1 hour (only when explicitly mentioned)
   - "today" → NOW() - 24 hours
   - "this week" → NOW() - 7 days

2. USERNAME HANDLING:
   - ALWAYS check BOTH fields: (user == "X" OR body_json.username == "X")
   - Login attempts → use body_json.username
   - Authenticated requests → use user

3. AGGREGATIONS (MUST use STATS for these):
   - "pie chart" / "show distribution" / "breakdown" → STATS count = COUNT(*) BY field
   - "top N" / "most active" / "most common" → STATS count = COUNT(*) BY field | SORT count DESC
   - "count" / "how many" / "total" → STATS total = COUNT(*)
   - "group by" / "categorize" → STATS COUNT(*) BY field
   
   KEY: When user asks for visualization (pie/bar chart) or distribution, ALWAYS use STATS!

4. SECURITY QUERIES:
   - "failed logins" → path == "/login" AND response_status == 401
   - "brute force" → STATS count BY client_ip/username + WHERE count > threshold
   - "suspicious activity" → response_status == 403 OR unusual patterns
   - "attacks" → high request rate, failed auth, scanning patterns

5. FIELD INTERPRETATION:
   - "user X" / "username X" → check both user and body_json.username
   - "from IP" / "IP address" → client_ip
   - "slow" / "performance issues" → processing_time_ms > 1000
   - "errors" → response_status >= 400 OR response_success == false
   - "POST data" / "request body" → body_json.* fields

6. LIMITS & SORTING:
   - Default LIMIT: 100
   - Aggregations: no LIMIT needed (already grouped)
   - Always SORT by timestamp DESC unless aggregating
   - For "top N" queries: SORT by count DESC + LIMIT N

Generate queries that:
- Default to last 24 hours if no time specified (most data is not real-time)
- Only use 1 hour when user explicitly says "last hour" or "past hour"
- Include reasonable LIMIT (default 100, max 1000)
- Use appropriate aggregations for "count", "find multiple", "detect" requests
- Handle security-focused queries (failed logins, attacks, suspicious activity)
- Check BOTH user fields when username is mentioned
- Return meaningful, actionable results
"""


# ============================================================================
# 3. LLM QUERY GENERATION
# ============================================================================

async def generate_esql_query(natural_language_query: str) -> Dict[str, Any]:
    """
    Call Groq LLM to generate ESQL query from natural language.
    
    Args:
        natural_language_query: User's natural language request
        
    Returns:
        Dictionary with generated query and metadata
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}'
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate an ESQL query for: {natural_language_query}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0
    }
    
    try:
        response = await http_client.post(
            GROQ_API_URL, 
            headers=headers, 
            json=payload, 
            timeout=30.0
        )
        response.raise_for_status()
        
        data = response.json()
        llm_output = data['choices'][0]['message']['content']
        
        # Parse JSON response
        result = json.loads(llm_output)
        
        return {
            "success": True,
            "natural_language": result.get("natural_language", natural_language_query),
            "esql_query": result.get("esql_query", ""),
            "explanation": result.get("explanation", ""),
            "estimated_results": result.get("estimated_results", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
        
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP error: {e.response.status_code}",
            "timestamp": datetime.now().isoformat()
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse LLM response: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


async def execute_esql_query(esql_query: str) -> Dict[str, Any]:
    """
    Execute an ESQL query against Elasticsearch and return raw results.
    
    Args:
        esql_query: The ESQL query string to execute
        
    Returns:
        Dictionary with execution results and raw data
    """
    if not elasticsearch_client:
        return {
            "success": False,
            "error": "Elasticsearch client not configured. Check ELASTICSEARCH_ENDPOINT and ELASTICSEARCH_API_KEY",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # Note: Elasticsearch Python client uses the query DSL API
        # ESQL is converted to query DSL or executed via _esql endpoint
        # For now, we'll convert common ESQL patterns to query DSL
        
        # Execute using Elasticsearch _esql API (ES 8.11+)
        response = await elasticsearch_client.perform_request(
            "POST",
            "/_query",
            body={"query": esql_query},
            headers={"Content-Type": "application/json"}
        )
        
        return {
            "success": True,
            "esql_query": esql_query,
            "raw_results": response.body,
            "columns": response.body.get("columns", []),
            "values": response.body.get("values", []),
            "total_rows": len(response.body.get("values", [])),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Fallback: Try to convert ESQL to Query DSL and execute
        try:
            # Parse simple ESQL to Query DSL (basic conversion)
            query_dsl = convert_esql_to_dsl(esql_query)
            
            # Extract size from query_dsl if present, otherwise use default
            query_size = query_dsl.pop("size", 100)
            
            result = await elasticsearch_client.search(
                index="api_requests",
                body=query_dsl,
                size=query_size
            )
            
            return {
                "success": True,
                "esql_query": esql_query,
                "query_dsl_used": query_dsl,
                "raw_results": result.body,
                "hits": result["hits"]["hits"],
                "total_hits": result["hits"]["total"]["value"],
                "aggregations": result.get("aggregations", {}),
                "timestamp": datetime.now().isoformat(),
                "note": "Executed using Query DSL conversion (ESQL API not available)"
            }
            
        except Exception as fallback_error:
            return {
                "success": False,
                "error": f"ESQL execution failed: {str(e)}. DSL fallback also failed: {str(fallback_error)}",
                "esql_query": esql_query,
                "timestamp": datetime.now().isoformat()
            }


def convert_esql_to_dsl(esql_query: str) -> Dict[str, Any]:
    """
    Convert simple ESQL queries to Elasticsearch Query DSL.
    This is a basic converter for common patterns.
    """
    from datetime import timedelta
    import re
    
    query_dsl = {
        "query": {"bool": {"must": []}},
        "size": 100,
        "sort": [{"timestamp": {"order": "desc"}}]
    }
    
    # Extract time range
    time_match = re.search(r'NOW\(\)\s*-\s*(\d+)\s*(hour|hours|day|days)', esql_query, re.IGNORECASE)
    if time_match:
        value = int(time_match.group(1))
        unit = time_match.group(2).lower()
        
        if 'hour' in unit:
            hours = value
        elif 'day' in unit:
            hours = value * 24
        else:
            hours = 1
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query_dsl["query"]["bool"]["must"].append({
            "range": {
                "timestamp": {
                    "gte": start_time.isoformat(),
                    "lte": end_time.isoformat()
                }
            }
        })
    
    # Extract field == value conditions
    field_matches = re.findall(r'(\w+)\s*==\s*["\']?([^"\'|\s]+)["\']?', esql_query)
    for field, value in field_matches:
        # Convert boolean strings
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.isdigit():
            value = int(value)
        
        # Use .keyword for string fields
        if isinstance(value, str) and field not in ["response_status", "client_port", "processing_time_ms"]:
            field = f"{field}.keyword"
        
        query_dsl["query"]["bool"]["must"].append({
            "term": {field: value}
        })
    
    # Extract LIMIT
    limit_match = re.search(r'LIMIT\s+(\d+)', esql_query, re.IGNORECASE)
    if limit_match:
        query_dsl["size"] = int(limit_match.group(1))
    
    # Extract STATS for aggregations
    if "STATS" in esql_query.upper():
        query_dsl["size"] = 10  # Return sample documents for context + aggregations
        query_dsl["aggs"] = {}
        
        # Simple COUNT(*) BY field
        stats_match = re.search(r'STATS\s+(\w+)\s*=\s*COUNT\(\*\)\s+BY\s+(\w+)', esql_query, re.IGNORECASE)
        if stats_match:
            agg_name = stats_match.group(1)
            field = stats_match.group(2)
            
            # Use .keyword for text fields, but not for numeric/boolean fields
            keyword_suffix = ".keyword" if field not in ["response_status", "client_port", "processing_time_ms", "body_size", "response_success"] else ""
            
            query_dsl["aggs"][agg_name] = {
                "terms": {
                    "field": f"{field}{keyword_suffix}",
                    "size": 100  # Return top 100 unique values
                }
            }
    
    return query_dsl


# ============================================================================
# 4. QUERY TEMPLATES FOR COMMON PATTERNS
# ============================================================================

QUERY_TEMPLATES = {
    "failed_logins": """
FROM api_requests
| WHERE timestamp >= NOW() - {hours} hours
  AND path == "/login"
  AND response_status == 401
| LIMIT {limit}
""",
    
    "suspicious_ips": """
FROM api_requests
| WHERE timestamp >= NOW() - {hours} hours
  AND response_success == false
| STATS count = COUNT(*) BY client_ip
| WHERE count > {threshold}
| SORT count DESC
""",
    
    "user_activity": """
FROM api_requests
| WHERE timestamp >= NOW() - {hours} hours
  AND username == "{username}"
| LIMIT {limit}
""",
    
    "slow_requests": """
FROM api_requests
| WHERE timestamp >= NOW() - {hours} hours
  AND processing_time_ms >= {min_time}
| SORT processing_time_ms DESC
| LIMIT {limit}
""",
    
    "endpoint_stats": """
FROM api_requests
| WHERE timestamp >= NOW() - {hours} hours
| STATS 
    count = COUNT(*),
    avg_time = AVG(processing_time_ms),
    success_rate = AVG(CASE(response_success, 1, 0))
  BY path
| SORT count DESC
| LIMIT {limit}
"""
}


async def detect_template_query(query: str) -> tuple[str, Dict[str, Any]]:
    """
    Detect if query matches a common template pattern.
    
    Returns:
        (template_name, parameters) or (None, {})
    """
    query_lower = query.lower()
    
    # Failed logins detection
    if any(word in query_lower for word in ["failed login", "login attempt", "401"]):
        return ("failed_logins", {"hours": 1, "limit": 100})
    
    # Suspicious IPs detection
    if any(word in query_lower for word in ["suspicious", "attack", "brute force", "multiple attempt"]):
        return ("suspicious_ips", {"hours": 1, "threshold": 10})
    
    # User activity detection
    if "user" in query_lower and ("activity" in query_lower or "requests" in query_lower):
        # Try to extract username
        import re
        username_match = re.search(r'user[:\s]+(\w+)', query_lower)
        username = username_match.group(1) if username_match else "admin"
        return ("user_activity", {"hours": 24, "username": username, "limit": 100})
    
    # Slow requests detection
    if any(word in query_lower for word in ["slow", "performance", "latency"]):
        return ("slow_requests", {"hours": 24, "min_time": 1000, "limit": 50})
    
    # Endpoint stats detection
    if any(word in query_lower for word in ["endpoint", "api stats", "most used"]):
        return ("endpoint_stats", {"hours": 24, "limit": 10})
    
    return (None, {})


# ============================================================================
# 5. AGENT EVENT HANDLERS
# ============================================================================

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("[ESQL AGENT] Elasticsearch Query Generator online, ready to generate ESQL queries.")


@chat_protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handle incoming chat messages and generate ESQL queries.
    """
    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(),
            acknowledged_msg_id=msg.msg_id
        ),
    )
    
    # Collect text from message
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    ctx.logger.info(f"[ESQL AGENT] Received query: {text}")
    
    # Check if it's a template query first (faster)
    template_name, params = await detect_template_query(text)
    
    if template_name:
        ctx.logger.info(f"[ESQL AGENT] Matched template: {template_name}")
        esql_query = QUERY_TEMPLATES[template_name].format(**params)
        
        response_data = {
            "success": True,
            "natural_language": text,
            "esql_query": esql_query.strip(),
            "explanation": f"Generated from {template_name} template",
            "estimated_results": "medium",
            "method": "template",
            "timestamp": datetime.now().isoformat()
        }
    else:
        # Use LLM for complex queries
        ctx.logger.info("[ESQL AGENT] Generating query with LLM...")
        start_time = time.time()
        response_data = await generate_esql_query(text)
        latency = time.time() - start_time
        ctx.logger.info(f"[ESQL AGENT] Query generated in {latency:.2f}s")
        response_data["method"] = "llm"
    
    # Execute the query and get raw results
    if response_data.get("success"):
        ctx.logger.info("[ESQL AGENT] Executing query against Elasticsearch...")
        execution_result = await execute_esql_query(response_data["esql_query"])
        
        # Merge execution results with generation results
        response_data["execution"] = execution_result
        
        if execution_result.get("success"):
            ctx.logger.info(f"[ESQL AGENT] Query executed successfully. Rows: {execution_result.get('total_hits', execution_result.get('total_rows', 0))}")
        else:
            ctx.logger.error(f"[ESQL AGENT] Query execution failed: {execution_result.get('error')}")
    
    # Format response as JSON string
    response_text = json.dumps(response_data, indent=2)
    
    # Send response back
    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response_text),
                EndSessionContent(type="end-session"),
            ]
        )
    )


@chat_protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements."""
    pass


# Include chat protocol
agent.include(chat_protocol, publish_manifest=True)


# ============================================================================
# 6. REST API ENDPOINTS
# ============================================================================

class QueryRequest(Model):
    """Request model for REST API."""
    query: str


class QueryResponse(Model):
    """Response model for REST API."""
    success: bool
    data: Optional[Dict[str, Any]] = {}
    error: Optional[str] = None


@agent.on_rest_post("/generate", QueryRequest, QueryResponse)
async def handle_rest_query(ctx: Context, request: QueryRequest) -> QueryResponse:
    """
    REST endpoint for generating and executing ESQL queries.
    
    Example:
        POST http://localhost:8002/generate
        {"query": "Show failed logins in the last hour"}
    
    Returns:
        - Generated ESQL query
        - Execution results with raw data
    """
    try:
        # Check template first
        template_name, params = await detect_template_query(request.query)
        
        if template_name:
            esql_query = QUERY_TEMPLATES[template_name].format(**params)
            data = {
                "success": True,
                "natural_language": request.query,
                "esql_query": esql_query.strip(),
                "explanation": f"Generated from {template_name} template",
                "method": "template",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Use LLM
            data = await generate_esql_query(request.query)
        
        # Execute the query and get raw results
        if data.get("success"):
            ctx.logger.info("[ESQL AGENT REST] Executing query...")
            execution_result = await execute_esql_query(data["esql_query"])
            data["execution"] = execution_result
            
            if execution_result.get("success"):
                ctx.logger.info(f"[ESQL AGENT REST] Execution successful. Results: {execution_result.get('total_hits', execution_result.get('total_rows', 0))} rows")
            else:
                ctx.logger.error(f"[ESQL AGENT REST] Execution failed: {execution_result.get('error')}")
        
        return QueryResponse(success=True, data=data)
        
    except Exception as e:
        ctx.logger.error(f"[ESQL AGENT] Error: {str(e)}")
        return QueryResponse(success=False, error=str(e))


# ============================================================================
# 7. EVENT HANDLERS
# ============================================================================

@agent.on_event("startup")
async def on_startup(ctx: Context):
    """Run on agent startup."""
    ctx.logger.info("[ESQL AGENT] Elasticsearch Query Generator online")
    ctx.logger.info(f"[ESQL AGENT] REST API: http://localhost:8006/generate")
    
    if elasticsearch_client:
        try:
            ping = await elasticsearch_client.ping()
            if ping:
                ctx.logger.info("[ESQL AGENT] ✓ Elasticsearch connected")
            else:
                ctx.logger.warning("[ESQL AGENT] ✗ Elasticsearch ping failed")
        except Exception as e:
            ctx.logger.error(f"[ESQL AGENT] Elasticsearch connection error: {str(e)}")
    else:
        ctx.logger.warning("[ESQL AGENT] Elasticsearch client not configured")


@agent.on_event("shutdown")
async def on_shutdown(ctx: Context):
    """Run on agent shutdown."""
    ctx.logger.info("[ESQL AGENT] Shutting down...")
    
    # Close HTTP client
    await http_client.aclose()
    
    # Close Elasticsearch client
    if elasticsearch_client:
        await elasticsearch_client.close()
    
    ctx.logger.info("[ESQL AGENT] Shutdown complete")


# ============================================================================
# 8. RUN AGENT
# ============================================================================

if __name__ == "__main__":
    agent.run()

