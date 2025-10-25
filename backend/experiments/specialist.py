from typing import List, Dict, Optional
import os, requests, json

SYSTEM_PROMPT = """You are an expert API security analyst. Analyze the batch of API requests for security threats and suspicious patterns.

Look for:
- Brute force attacks (repeated failed auth attempts)
- Credential stuffing (multiple login attempts with different credentials)
- Rate limit abuse (high frequency requests from same source)
- Endpoint enumeration/scanning (requests to many different endpoints)
- SQL injection attempts (suspicious query parameters)
- Admin panel probing (unauthorized access attempts to admin endpoints)
- Suspicious user agents (bots, scanners, outdated browsers)
- Data exfiltration patterns (large response sizes, bulk data access)
- Geographic anomalies (requests from unusual locations)
- Time-based anomalies (unusual request patterns/timing)

Respond with a JSON object containing:
{
  "threat_level": "none|low|medium|high|critical",
  "threats_detected": [
    {
      "type": "brute_force|credential_stuffing|rate_abuse|scanning|injection|unauthorized_access|suspicious_agent|data_exfiltration|geographic_anomaly|timing_anomaly",
      "severity": "low|medium|high|critical",
      "description": "Brief description",
      "affected_ips": ["ip1", "ip2"],
      "affected_endpoints": ["/endpoint1"],
      "evidence": ["specific evidence from logs"],
      "recommendation": "Suggested mitigation action"
    }
  ],
  "summary": "Overall security assessment",
  "statistics": {
    "total_requests": 0,
    "failed_auth_attempts": 0,
    "unique_ips": 0,
    "unique_endpoints": 0,
    "suspicious_requests": 0
    }
  }"""

AUTHENTICATION_SPECIALIST_PROMPT = """You are an AI security specialist focused specifically on AUTHENTICATION endpoints (e.g., /login, /auth, /password-reset).

Your responsibilities:
1. Review the provided incident or API activity context.
2. Identify suspicious users or IPs related to authentication misuse.
3. Recommend appropriate mitigations in a JSON list, where each list entry is:
   {
     "entity_type": "user" or "ip",
     "entity": "<username or ip_address>",
     "severity": "low|medium|high|critical",
     "mitigation": "short instruction such as throttle login, require MFA, block temporarily"
   }

Optional additional context:
- You have access to a single callable tool:
  {
    "name": "fetch_from_elasticsearch",
    "description": "Query authentication-related logs from Elasticsearch for deeper context.",
    "parameters": {
      "type": "object",
      "properties": {
        "query_string": { "type": "string", "description": "The specific ES query you want to run." }
      },
      "required": ["query_string"]
    }
  }

If you believe additional context is required (e.g., failed login frequency, token anomalies, known breached IPs), you may call "fetch_from_elasticsearch" ONCE with a specific query such as:
  {
    "query_string": "failed_logins for user X in last 10m"
  }

Then wait for the tool response before continuing with mitigation output.

When ready to deliver the final result, return ONLY a JSON array of mitigation entries as specified.
Do NOT include extra commentary outside of JSON in your final output."""

# Elasticsearch tool definition for specialist agents
ES_TOOL = {
    "type": "function",
    "function": {
        "name": "fetch_from_elasticsearch",
        "description": "Query logs from Elasticsearch for deeper context",
        "parameters": {
            "type": "object",
            "properties": {
                "query_string": {
                    "type": "string",
                    "description": "The specific ES query to run"
                }
            },
            "required": ["query_string"]
        }
    }
}

# Elasticsearch query function that is provided optionally to the specialist agents in initial call
def fetch_from_elasticsearch(query_string: str) -> Dict:
    """Stub for Elasticsearch query. In production, connect to real ES cluster."""
    print(f"[ES Query] {query_string}")
    
    # Return mock data based on query patterns
    if "failed_login" in query_string.lower():
        return {
            "hits": 15,
            "pattern": "Multiple failed login attempts detected",
            "time_range": "last 10m",
            "details": "User attempted login 15 times with wrong password"
        }
    elif "query" in query_string.lower() or "search" in query_string.lower():
        return {
            "hits": 250,
            "pattern": "High-volume search queries",
            "time_range": "last 1h",
            "details": "Unusual search pattern detected: systematic enumeration"
        }
    else:
        return {
            "hits": 0,
            "message": "No matching logs found"
        }

# function to analyze authentication threats and get mitigation recommendations
def analyze_authentication_threats(
    incident_context: str | Dict,
    *,
    model: str = "llama-3.3-70b-versatile",
    timeout: float = 30.0
) -> List[Dict]:
    """Analyze authentication-related threats and get mitigation recommendations.
    
    Args:
        incident_context: Context about the authentication incident (string or dict)
        model: Groq model to use
        timeout: Request timeout in seconds
        
    Returns:
        List of mitigation recommendations with entity, severity, and actions
        
    Example:
        >>> incident = "User 'admin' had 20 failed login attempts from IP 1.2.3.4"
        >>> mitigations = analyze_authentication_threats(incident)
        >>> print(mitigations)
        [{"entity_type": "ip", "entity": "1.2.3.4", "severity": "high", 
          "mitigation": "Block temporarily for brute force attack"}]
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY environment variable")
    
    # Convert context to string if needed
    if isinstance(incident_context, dict):
        context_text = json.dumps(incident_context, indent=2)
    else:
        context_text = incident_context
    
    messages = [
        {"role": "system", "content": AUTHENTICATION_SPECIALIST_PROMPT},
        {"role": "user", "content": f"Analyze this authentication incident and provide mitigation recommendations:\n\n{context_text}"}
    ]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # First call - agent may request ES tool
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "tools": [ES_TOOL],
        "tool_choice": "auto"
    }
    
    resp = requests.post(url, headers=headers, json=body, timeout=timeout)
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    
    result = resp.json()
    message = result["choices"][0]["message"]
    
    # Check if agent wants to call ES tool
    tool_calls = message.get("tool_calls", [])
    
    if tool_calls:
        print(f"[Auth Agent] Requesting ES query...")
        
        # Execute ES tool
        for tool_call in tool_calls:
            if tool_call["function"]["name"] == "fetch_from_elasticsearch":
                args = json.loads(tool_call["function"]["arguments"])
                es_result = fetch_from_elasticsearch(args["query_string"])
                
                # Add tool result to conversation
                messages.append({
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "tool_calls": tool_calls
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(es_result)
                })
        
        # Second call - get final recommendations
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"}
        }
        
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code != 200:
            resp.raise_for_status()
        
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
    else:
        # No tool call needed, get content directly
        content = message.get("content", "[]")
    
    # Parse JSON response
    try:
        # Handle both raw array and object with 'mitigations' key
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "mitigations" in parsed:
            return parsed["mitigations"]
        else:
            return []
    except json.JSONDecodeError:
        print(f"Failed to parse response: {content}")
        return []

# function to analyze search endpoint threats and get mitigation recommendations
def analyze_search_endpoint_threats(
    incident_context: str | Dict,
    *,
    model: str = "llama-3.3-70b-versatile",
    timeout: float = 30.0
) -> List[Dict]:
    """Analyze search endpoint abuse and get mitigation recommendations.
    
    Args:
        incident_context: Context about the search endpoint incident
        model: Groq model to use
        timeout: Request timeout in seconds
        
    Returns:
        List of mitigation recommendations for search endpoint abuse
        
    Example:
        >>> incident = "IP 5.6.7.8 made 500 search queries in 1 minute"
        >>> mitigations = analyze_search_endpoint_threats(incident)
        >>> print(mitigations)
        [{"entity_type": "ip", "entity": "5.6.7.8", "severity": "high",
          "mitigation": "Apply rate-limiting for scraping behavior"}]
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY environment variable")
    
    # Convert context to string if needed
    if isinstance(incident_context, dict):
        context_text = json.dumps(incident_context, indent=2)
    else:
        context_text = incident_context
    
    messages = [
        {"role": "system", "content": SEARCH_SPECIALIST_PROMPT},
        {"role": "user", "content": f"Analyze this search endpoint incident and provide mitigation recommendations:\n\n{context_text}"}
    ]
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # First call - agent may request ES tool
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "tools": [ES_TOOL],
        "tool_choice": "auto"
    }
    
    resp = requests.post(url, headers=headers, json=body, timeout=timeout)
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    
    result = resp.json()
    message = result["choices"][0]["message"]
    
    # Check if agent wants to call ES tool
    tool_calls = message.get("tool_calls", [])
    
    if tool_calls:
        print(f"[Search Agent] Requesting ES query...")
        
        # Execute ES tool
        for tool_call in tool_calls:
            if tool_call["function"]["name"] == "fetch_from_elasticsearch":
                args = json.loads(tool_call["function"]["arguments"])
                es_result = fetch_from_elasticsearch(args["query_string"])
                
                # Add tool result to conversation
                messages.append({
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "tool_calls": tool_calls
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(es_result)
                })
        
        # Second call - get final recommendations
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"}
        }
        
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code != 200:
            resp.raise_for_status()
        
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
    else:
        # No tool call needed, get content directly
        content = message.get("content", "[]")
    
    # Parse JSON response
    try:
        # Handle both raw array and object with 'mitigations' key
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "mitigations" in parsed:
            return parsed["mitigations"]
        else:
            return []
    except json.JSONDecodeError:
        print(f"Failed to parse response: {content}")
        return []