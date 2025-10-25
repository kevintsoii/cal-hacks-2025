"""
Elasticsearch Tool for Fetch.ai Agents
A standalone tool that agents can call to query the Elasticsearch database.
Supports dynamic queries based on any field in the api_requests index.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, timezone
from elasticsearch import AsyncElasticsearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def query_elasticsearch_dynamic(
    query_params: Dict[str, Any],
    time_range_hours: int = 1,
    size: int = 100
) -> Dict[str, Any]:
    """
    Dynamic Elasticsearch query that can search by any field in the api_requests index.
    Automatically handles different field types and builds the appropriate query.
    
    Supported fields from your data structure:
    - username, user, user_id (string)
    - client_ip, client_port (string/number)
    - method (GET, POST, etc.)
    - path, full_url (string)
    - response_status (200, 401, etc.)
    - response_success (true/false)
    - body_json.* (nested fields like body_json.username, body_json.password)
    - origin, referer (string)
    - content_type (string)
    - processing_time_ms (number - supports range queries)
    
    Args:
        query_params: Dictionary of field:value pairs to search for
            Examples:
                {"username": "admin"}
                {"response_status": 401}
                {"client_ip": "192.168.65.1"}
                {"method": "POST", "path": "/login"}
                {"response_success": False}
                {"processing_time_ms": {"gte": 100}}  # Range query
        time_range_hours: Number of hours to look back (minimum 1 hour)
        size: Number of documents to return
    
    Returns:
        Dictionary containing query results and aggregations
    """
    try:
        # Enforce minimum 1 hour
        if time_range_hours < 1:
            time_range_hours = 1
        
        # Get Elasticsearch credentials from environment
        es_endpoint = os.getenv("ELASTICSEARCH_ENDPOINT")
        es_api_key = os.getenv("ELASTICSEARCH_API_KEY")
        
        if not es_endpoint or not es_api_key:
            return {
                "success": False,
                "error": "Elasticsearch credentials not configured"
            }
        
        # Initialize Elasticsearch client
        es_client = AsyncElasticsearch(
            es_endpoint,
            api_key=es_api_key,
            verify_certs=True,
            request_timeout=30
        )
        
        # Build query conditions
        must_conditions = []
        
        # Add time range filter (mandatory, minimum 1 hour)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_range_hours)
        must_conditions.append({
            "range": {
                "timestamp": {
                    "gte": start_time.isoformat(),
                    "lte": end_time.isoformat()
                }
            }
        })
        
        # Process query parameters dynamically
        for field, value in query_params.items():
            # Handle range queries (e.g., processing_time_ms >= 100)
            if isinstance(value, dict) and any(k in value for k in ["gte", "lte", "gt", "lt"]):
                must_conditions.append({
                    "range": {field: value}
                })
            # Handle boolean values
            elif isinstance(value, bool):
                must_conditions.append({
                    "term": {field: value}
                })
            # Handle numeric values (status codes, ports, etc.)
            elif isinstance(value, (int, float)):
                must_conditions.append({
                    "term": {field: value}
                })
            # Handle string values (use .keyword for exact match)
            elif isinstance(value, str):
                # For nested fields like body_json.username
                if "." in field:
                    must_conditions.append({
                        "term": {field: value}
                    })
                else:
                    # Try keyword field first for exact match
                    must_conditions.append({
                        "term": {f"{field}.keyword": value}
                    })
            # Handle list values (match any)
            elif isinstance(value, list):
                must_conditions.append({
                    "terms": {f"{field}.keyword" if isinstance(value[0], str) else field: value}
                })
        
        # Build query body
        query_body = {
            "query": {
                "bool": {
                    "must": must_conditions
                }
            },
            "size": size,
            "sort": [
                {"timestamp": {"order": "desc"}}
            ]
        }
        
        # Add useful aggregations automatically
        query_body["aggs"] = {
            "unique_ips": {
                "cardinality": {"field": "client_ip.keyword"}
            },
            "unique_users": {
                "cardinality": {"field": "username.keyword"}
            },
            "status_codes": {
                "terms": {"field": "response_status", "size": 10}
            },
            "methods": {
                "terms": {"field": "method.keyword", "size": 10}
            },
            "top_paths": {
                "terms": {"field": "path.keyword", "size": 10}
            }
        }
        
        # Execute query
        result = await es_client.search(
            index="api_requests",
            body=query_body
        )
        
        # Close connection
        await es_client.close()
        
        # Format response
        response = {
            "success": True,
            "query_params": query_params,
            "time_range": f"Last {time_range_hours} hours",
            "total_hits": result["hits"]["total"]["value"],
            "documents": [hit["_source"] for hit in result["hits"]["hits"]],
            "aggregations": {
                "unique_ips": result["aggregations"]["unique_ips"]["value"],
                "unique_users": result["aggregations"]["unique_users"]["value"],
                "status_codes": result["aggregations"]["status_codes"]["buckets"],
                "methods": result["aggregations"]["methods"]["buckets"],
                "top_paths": result["aggregations"]["top_paths"]["buckets"]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error querying Elasticsearch: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def query_failed_logins(
    time_range_hours: int = 1,
    username: Optional[str] = None,
    client_ip: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query failed login attempts (response_status 401 and path /login).
    
    Args:
        time_range_hours: Number of hours to look back (minimum 1)
        username: Filter by specific username (optional)
        client_ip: Filter by specific IP (optional)
    
    Returns:
        Failed login attempts with details
    """
    query_params = {
        "path": "/login",
        "response_status": 401,
        "response_success": False
    }
    
    if username:
        query_params["username"] = username
    if client_ip:
        query_params["client_ip"] = client_ip
    
    return await query_elasticsearch_dynamic(
        query_params=query_params,
        time_range_hours=time_range_hours,
        size=100
    )


async def query_suspicious_activity(
    time_range_hours: int = 1,
    min_requests: int = 10
) -> Dict[str, Any]:
    """
    Query for suspicious activity patterns (multiple failed attempts, etc.).
    
    Args:
        time_range_hours: Number of hours to look back (minimum 1)
        min_requests: Minimum number of requests to be considered suspicious
    
    Returns:
        Suspicious activity data
    """
    # Query all failed attempts
    failed_attempts = await query_elasticsearch_dynamic(
        query_params={"response_success": False},
        time_range_hours=time_range_hours,
        size=1000
    )
    
    if not failed_attempts["success"]:
        return failed_attempts
    
    # Analyze patterns
    ip_counts = {}
    user_counts = {}
    
    for doc in failed_attempts["documents"]:
        ip = doc.get("client_ip", "unknown")
        user = doc.get("username", "unknown")
        
        ip_counts[ip] = ip_counts.get(ip, 0) + 1
        user_counts[user] = user_counts.get(user, 0) + 1
    
    # Find suspicious IPs and users
    suspicious_ips = {ip: count for ip, count in ip_counts.items() if count >= min_requests}
    suspicious_users = {user: count for user, count in user_counts.items() if count >= min_requests}
    
    return {
        "success": True,
        "time_range": f"Last {time_range_hours} hours",
        "total_failed_attempts": failed_attempts["total_hits"],
        "suspicious_ips": suspicious_ips,
        "suspicious_users": suspicious_users,
        "details": failed_attempts["documents"][:50],  # Return first 50 for details
        "timestamp": datetime.utcnow().isoformat()
    }


async def query_user_activity(
    username: str,
    time_range_hours: int = 1
) -> Dict[str, Any]:
    """
    Query all activity for a specific user.
    
    Args:
        username: Username to search for
        time_range_hours: Number of hours to look back (minimum 1)
    
    Returns:
        User activity data
    """
    return await query_elasticsearch_dynamic(
        query_params={"username": username},
        time_range_hours=time_range_hours,
        size=100
    )


async def query_by_ip(
    client_ip: str,
    time_range_hours: int = 1
) -> Dict[str, Any]:
    """
    Query all activity from a specific IP address.
    
    Args:
        client_ip: IP address to search for
        time_range_hours: Number of hours to look back (minimum 1)
    
    Returns:
        IP activity data
    """
    return await query_elasticsearch_dynamic(
        query_params={"client_ip": client_ip},
        time_range_hours=time_range_hours,
        size=100
    )


async def query_slow_requests(
    min_processing_time_ms: int = 1000,
    time_range_hours: int = 1
) -> Dict[str, Any]:
    """
    Query requests that took longer than specified time to process.
    
    Args:
        min_processing_time_ms: Minimum processing time in milliseconds
        time_range_hours: Number of hours to look back (minimum 1)
    
    Returns:
        Slow requests data
    """
    return await query_elasticsearch_dynamic(
        query_params={"processing_time_ms": {"gte": min_processing_time_ms}},
        time_range_hours=time_range_hours,
        size=100
    )


# Example usage (for testing only)
if __name__ == "__main__":
    import asyncio
    
    async def test_tool():
        """Test the Elasticsearch tool"""
        
        print("1. Testing dynamic query - failed logins...")
        result1 = await query_failed_logins(time_range_hours=24)
        print(f"Failed logins: {result1.get('total_hits', 0)} found\n")
        
        print("2. Testing dynamic query - specific user...")
        result2 = await query_user_activity(username="admin", time_range_hours=24)
        print(f"Admin activity: {result2.get('total_hits', 0)} requests\n")
        
        print("3. Testing dynamic query - suspicious activity...")
        result3 = await query_suspicious_activity(time_range_hours=24, min_requests=5)
        print(f"Suspicious IPs: {result3.get('suspicious_ips', {})}\n")
        
        print("4. Testing dynamic query - slow requests...")
        result4 = await query_slow_requests(min_processing_time_ms=100, time_range_hours=24)
        print(f"Slow requests: {result4.get('total_hits', 0)} found\n")
        
        print("5. Testing custom dynamic query...")
        result5 = await query_elasticsearch_dynamic(
            query_params={
                "method": "POST",
                "response_status": 401,
                "path": "/login"
            },
            time_range_hours=24
        )
        print(f"Custom query: {result5.get('total_hits', 0)} hits\n")
    
    asyncio.run(test_tool())