"""
AI Chatbot Agent for Security Dashboard
Uses ESQL Query Agent + Groq LLM to answer natural language questions about API security data.
"""

import os
import asyncio
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model

from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

# Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
ESQL_AGENT_URL = "http://localhost:8006/generate"

# Chatbot Agent
agent = Agent(
    name="Security Chatbot",
    seed="security_chatbot_seed_12345",
    port=8007,
    mailbox=True,
    publish_agent_details=True
)

# Chat protocol
chat_protocol = Protocol(spec=chat_protocol_spec)

# HTTP client for API calls
http_client = httpx.AsyncClient(timeout=30.0)

# Conversation memory (stores last 10 messages per session)
conversation_history: Dict[str, List[Dict[str, str]]] = {}


class QueryRequest(Model):
    """User query request."""
    query: str
    session_id: Optional[str] = "default"  # For tracking conversation history


class QueryResponse(Model):
    """Chatbot response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    chart_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


async def query_elasticsearch(natural_language: str, ctx=None) -> Dict[str, Any]:
    """
    Query Elasticsearch using the ESQL Query Agent.
    
    Args:
        natural_language: Natural language query
        ctx: Context for logging (optional)
        
    Returns:
        Dictionary with query results
    """
    try:
        if ctx:
            ctx.logger.info(f"Sending query to ESQL Agent: {natural_language}")
        
        response = await http_client.post(
            ESQL_AGENT_URL,
            json={"query": natural_language},
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("data", {})
            
            if ctx:
                ctx.logger.info(f"ESQL Agent response keys: {list(data.keys())}")
                if "execution" in data:
                    exec_keys = list(data["execution"].keys())
                    ctx.logger.info(f"Execution keys: {exec_keys}")
            
            return data
        else:
            error_msg = f"ESQL Agent returned {response.status_code}"
            if ctx:
                ctx.logger.error(error_msg)
            return {"error": error_msg}
            
    except Exception as e:
        error_msg = f"Failed to query Elasticsearch: {str(e)}"
        if ctx:
            ctx.logger.error(error_msg)
        return {"error": error_msg}


async def generate_ai_response(user_query: str, es_data: Dict[str, Any], ctx=None, conversation_context: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Generate intelligent response using Groq LLM based on Elasticsearch results.
    
    Args:
        user_query: Original user question
        es_data: Data returned from Elasticsearch
        ctx: Context for logging (optional)
        
    Returns:
        Dictionary with AI response and optional chart data
    """
    if not GROQ_API_KEY:
        return {
            "message": "AI analysis not available (missing API key)",
            "chart_data": None
        }
    
    # Extract the raw results - handle both ESQL and Query DSL formats
    execution = es_data.get("execution", {})
    raw_results = execution.get("raw_results", {})
    
    # Check which format we received - be more robust
    hits = []
    total_hits = 0
    aggregations = {}
    
    # Try multiple extraction paths
    if "hits" in execution:
        # Query DSL format (fallback) - direct in execution
        hits = execution.get("hits", [])
        total_hits = execution.get("total_hits", 0)
        aggregations = execution.get("aggregations", {})
    elif "hits" in raw_results:
        # Query DSL nested in raw_results
        hits_data = raw_results.get("hits", {})
        if isinstance(hits_data, dict):
            hits = hits_data.get("hits", [])
            total_hits = hits_data.get("total", {}).get("value", 0)
        else:
            hits = hits_data if isinstance(hits_data, list) else []
            total_hits = len(hits)
        aggregations = raw_results.get("aggregations", {})
    
    # If still no hits, try ESQL format (columns and values)
    if not hits:
        total_hits = execution.get("total_rows", 0) or execution.get("total_hits", 0)
        
        # Convert ESQL format to hits format for the LLM
        columns = execution.get("columns", [])
        values = execution.get("values", [])
        
        if columns and values:
            # Convert each row to a document
            for row in values[:20]:  # Get more samples for better analysis
                doc = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        col_name = col.get("name", f"col_{i}") if isinstance(col, dict) else f"col_{i}"
                        doc[col_name] = row[i]
                hits.append({"_source": doc})
    
    # Extract actual data from hits for better context
    sample_sources = [hit.get("_source", {}) for hit in hits[:20]]  # Get more samples
    
    # Debug logging
    if ctx:
        ctx.logger.info(f"Extracted {len(sample_sources)} sample documents from {total_hits} total hits")
        ctx.logger.info(f"Hits available: {len(hits)}")
        ctx.logger.info(f"Aggregations available: {bool(aggregations)}")
        
        if aggregations:
            ctx.logger.info(f"Aggregation keys: {list(aggregations.keys())}")
        
        if len(sample_sources) == 0 and not aggregations:
            ctx.logger.warning("WARNING: No sample sources AND no aggregations! Charts will be empty.")
            ctx.logger.warning(f"Execution keys: {list(execution.keys())}")
    
    # Build conversation context if available
    conversation_summary = ""
    if conversation_context and len(conversation_context) > 0:
        conversation_summary = "\n\nPrevious conversation:\n"
        for msg in conversation_context[-5:]:  # Last 5 messages
            conversation_summary += f"{msg['role']}: {msg['content'][:100]}...\n"
    
    # Build context with actual Elasticsearch data for Compound to visualize
    context = f"""You are a security analyst AI. A user asked: "{user_query}"{conversation_summary}

Elasticsearch returned {total_hits} total results.

Here is the ACTUAL data from Elasticsearch (first 10 documents):
{json.dumps(sample_sources, indent=2) if sample_sources else "ERROR: No sample data available"}

Aggregations (if available):
{json.dumps(aggregations, indent=2) if aggregations else "None"}

YOUR TASK:
1. Analyze the real data above and extract relevant values
2. If the user wants a chart, create a visualization using the ACTUAL data
3. For example: Count how many "method": "POST" vs "GET" appear in the sample
4. Use the data to provide insights and create meaningful visualizations
5. If there is truly no data (0 results, no documents, no aggregations), return chart_suggestion: null

Based on this ACTUAL data, provide:
1. A clear, concise answer to the user's question
2. Key insights and patterns you notice from the data
3. Security recommendations if relevant
4. If the user asks for charts/graphs, YOU MUST extract the actual data and create a chart

FORMATTING RULES for the "message" field:
- DO NOT use markdown formatting (**, __, #, etc.)
- Use plain text with clear structure
- Use numbers (1, 2, 3) for lists instead of bullets
- Use dashes (-) or arrows (→) for sub-items
- Use line breaks (\n) for spacing
- Use CAPS or "quotes" for emphasis instead of bold
- Make it readable as plain text in a web UI

GOOD formatting example:
"The top 5 most requested endpoints are:

1. /login - 2,617 requests
2. / - 381 requests  
3. /api/healthcheck - 40 requests
4. /api/settings - 39 requests
5. /api/users - 38 requests

The /login endpoint dominates with 79% of all traffic, which is typical for authentication-heavy applications."

BAD formatting example (DO NOT USE):
"**Top 5 endpoints:**
- **/login** – 2,617 requests
- **/** – 381 requests"

IMPORTANT CHART RULES:
- ONLY use chart types: "bar", "line", or "pie"
- ALWAYS extract REAL data from the Elasticsearch results above
- For PIE charts: Count occurrences in the sample data (e.g., count GET vs POST vs PUT methods)
- For BAR charts: Use aggregations if available, or manually count from sample data
- labels array must contain strings (e.g., "GET", "POST", IP addresses, endpoints)
- values array must contain actual numbers counted/extracted from the data
- If aggregations exist, parse them and use the buckets for chart data
- If sample data exists but no aggregations, manually count the values you want to chart
- NEVER return empty arrays or zeros - count the actual data!
- If truly no data exists, set chart_suggestion to null

EXAMPLE: If user asks "show me a pie chart of request types" and the sample data has:
- 5 documents with method: "GET"
- 2 documents with method: "POST"
- 1 document with method: "DELETE"

Then your chart should be:
{{
  "chart_suggestion": {{
    "type": "pie",
    "title": "Distribution of HTTP Request Methods",
    "data": {{
      "labels": ["GET", "POST", "DELETE"],
      "values": [5, 2, 1]
    }}
  }}
}}

Format your response as VALID JSON:
{{
  "message": "Your detailed analysis and answer (be specific about what you found). Use plain text formatting WITHOUT markdown symbols like **, __, or #. Instead, use clear structure with line breaks, dashes, and numbers. Make it readable as plain text.",
  "insights": ["specific insight from data", "another specific insight"],
  "recommendations": ["actionable recommendation", "another recommendation"],
  "chart_suggestion": {{
    "type": "bar",
    "title": "Descriptive Chart Title",
    "data": {{
      "labels": ["label1", "label2", "label3"],
      "values": [123, 456, 789]
    }}
  }}
}}

If no chart is appropriate or truly no data, set chart_suggestion to null.
"""
    
    try:
        response = await http_client.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "groq/compound",
                "messages": [
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            choice = result["choices"][0]
            ai_message = choice["message"]["content"]
            
            # Check if Compound generated a visualization (might have tool_calls or attachments)
            tool_calls = choice.get("tool_calls", [])
            
            if ctx:
                ctx.logger.info(f"Groq response has tool_calls: {len(tool_calls) > 0}")
            
            # Compound may include visualization output
            visualization_url = None
            for tool_call in tool_calls:
                if tool_call.get("type") == "visualization":
                    visualization_url = tool_call.get("output", {}).get("url")
            
            # Try to parse as JSON for structured response
            chart_data = None
            message_text = ai_message
            
            # Strip markdown code blocks if present
            cleaned_message = ai_message.strip()
            if cleaned_message.startswith("```"):
                # Remove opening ```json or ``` and closing ```
                lines = cleaned_message.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]  # Remove first line with ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]  # Remove last line with ```
                cleaned_message = '\n'.join(lines).strip()
            
            try:
                parsed = json.loads(cleaned_message)
                message_text = parsed.get("message", ai_message)
                chart_data = parsed.get("chart_suggestion")
                
                if ctx:
                    ctx.logger.info(f"Successfully parsed JSON response. Chart data present: {chart_data is not None}")
            except json.JSONDecodeError as e:
                # If not JSON, return as plain text
                if ctx:
                    ctx.logger.warning(f"Failed to parse AI response as JSON: {e}")
                    ctx.logger.debug(f"Raw message (first 200 chars): {ai_message[:200]}")
                message_text = ai_message
            
            return {
                "message": message_text,
                "chart_data": chart_data,
                "visualization_url": visualization_url  # For Compound-generated images
            }
        else:
            if ctx:
                ctx.logger.error(f"Groq API returned {response.status_code}: {response.text}")
            return {
                "message": f"Found {total_hits} results. Unable to generate visualization.",
                "chart_data": None
                }
            
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Error generating AI response: {e}")
        return {
            "message": f"Found {total_hits} results from Elasticsearch.",
            "chart_data": None
        }


@agent.on_rest_post("/query", QueryRequest, QueryResponse)
async def handle_query(ctx: Context, msg: QueryRequest):
    """
    Handle query requests via REST API.
    
    Process flow:
    1. Receive user's natural language query
    2. Convert to ESQL and execute via ESQL Agent
    3. Analyze results with LLM (with conversation context)
    4. Return intelligent response + optional chart data
    """
    ctx.logger.info(f"Chatbot received query: {msg.query}")
    session_id = msg.session_id or "default"
    
    # Initialize conversation history for this session if needed
    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    try:
        # Step 1: Query Elasticsearch using ESQL Agent
        ctx.logger.info("Querying Elasticsearch via ESQL Agent...")
        es_data = await query_elasticsearch(msg.query, ctx)
        
        if "error" in es_data:
            ctx.logger.error(f"ESQL Agent error: {es_data['error']}")
            return QueryResponse(
                success=False,
                message="Sorry, I couldn't process your query.",
                error=es_data["error"],
                timestamp=datetime.now().isoformat()
            )
        
        # Log data structure for debugging
        execution = es_data.get("execution", {})
        ctx.logger.info(f"Received execution data: success={execution.get('success')}, total_rows={execution.get('total_rows')}, total_hits={execution.get('total_hits')}")
        
        # Step 2: Generate AI response with conversation context
        ctx.logger.info("Generating AI response with LLM...")
        ai_response = await generate_ai_response(
            msg.query, 
            es_data, 
            ctx,
            conversation_history[session_id]
        )
        
        ctx.logger.info(f"AI response generated. Chart data: {ai_response.get('chart_data') is not None}")
        
        # Step 3: Update conversation history
        conversation_history[session_id].append({
            "role": "user",
            "content": msg.query
        })
        conversation_history[session_id].append({
            "role": "assistant",
            "content": ai_response["message"]
        })
        
        # Keep only last 20 messages (10 exchanges)
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]
        
        # Step 4: Return combined response
        return QueryResponse(
            success=True,
            message=ai_response["message"],
            data=es_data,
            chart_data=ai_response.get("chart_data"),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        ctx.logger.error(f"Error handling query: {e}")
        return QueryResponse(
            success=False,
            message="An error occurred while processing your request.",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@agent.on_event("startup")
async def startup(ctx: Context):
    """Log startup information."""
    ctx.logger.info(f"Security Chatbot Agent started on port 8007")
    ctx.logger.info(f"REST API available at: http://localhost:8007/query")
    ctx.logger.info(f"ESQL Agent endpoint: {ESQL_AGENT_URL}")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    """Cleanup on shutdown."""
    await http_client.aclose()
    ctx.logger.info("Chatbot agent shutting down")


if __name__ == "__main__":
    agent.run()

