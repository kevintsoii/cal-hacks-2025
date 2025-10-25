"""
Elasticsearch utilities for WebSocket real-time updates.
Handles initial data fetch and provides stats/anomaly detection.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from db.elasticsearch import elasticsearch_client

logger = logging.getLogger(__name__)


async def get_recent_logs(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the most recent logs from Elasticsearch.
    Used for initial WebSocket connection to send recent history.
    
    Args:
        limit: Number of recent logs to fetch (default: 10)
        
    Returns:
        List of document _source objects
    """
    if not elasticsearch_client.client:
        logger.warning("[ES] Elasticsearch client not available")
        return []
    
    try:
        query = {
            "query": {"match_all": {}},
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": limit
        }
        
        result = await elasticsearch_client.client.search(
            index="api_requests",
            body=query
        )
        
        hits = result.get("hits", {}).get("hits", [])
        documents = [hit["_source"] for hit in hits]
        
        logger.info(f"[ES] Fetched {len(documents)} recent logs for WebSocket client")
        return documents
        
    except Exception as e:
        logger.error(f"[ES] Error fetching recent logs: {e}")
        return []
    
async def get_recent_stats() -> Dict[str, Any]:
    """
    Get aggregated statistics with security metrics.
    
    Returns:
        Dictionary with statistics and security insights
    """
    if not elasticsearch_client.client:
        return {}
    
    try:
        # Query all documents for comprehensive stats
        query = {
            "query": {"match_all": {}},
            "aggs": {
                "total_requests": {
                    "value_count": {
                        "field": "timestamp"
                    }
                },
                "unique_ips": {
                    "cardinality": {
                        "field": "client_ip.keyword"
                    }
                },
                "unique_users": {
                    "cardinality": {
                        "field": "username.keyword"
                    }
                },
                "status_codes": {
                    "terms": {
                        "field": "response_status",
                        "size": 10
                    }
                },
                "top_endpoints": {
                    "terms": {
                        "field": "path.keyword",
                        "size": 10
                    }
                },
                "top_ips": {
                    "terms": {
                        "field": "client_ip.keyword",
                        "size": 10,
                        "order": {"_count": "desc"}
                    }
                },
                "top_failed_usernames": {
                    "filter": {
                        "term": {"response_success": False}
                    },
                    "aggs": {
                        "usernames": {
                            "terms": {
                                "field": "username.keyword",
                                "size": 10
                            }
                        }
                    }
                },
                "failed_requests": {
                    "filter": {
                        "term": {
                            "response_success": False
                        }
                    }
                },
                "http_methods": {
                    "terms": {
                        "field": "method.keyword",
                        "size": 10
                    }
                },
                "avg_response_time": {
                    "avg": {
                        "field": "processing_time_ms"
                    }
                }
            },
            "size": 0
        }
        
        result = await elasticsearch_client.client.search(
            index="api_requests",
            body=query
        )
        
        aggs = result.get("aggregations", {})
        
        return {
            "total_requests": result.get("hits", {}).get("total", {}).get("value", 0),
            "unique_ips": aggs.get("unique_ips", {}).get("value", 0),
            "unique_users": aggs.get("unique_users", {}).get("value", 0),
            "failed_requests": aggs.get("failed_requests", {}).get("doc_count", 0),
            "avg_response_time_ms": round(aggs.get("avg_response_time", {}).get("value", 0), 2),
            "status_codes": [
                {"code": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get("status_codes", {}).get("buckets", [])
            ],
            "top_endpoints": [
                {"endpoint": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get("top_endpoints", {}).get("buckets", [])
            ],
            "top_ips": [
                {"ip": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get("top_ips", {}).get("buckets", [])
            ],
            "top_failed_usernames": [
                {"username": bucket["key"], "failed_attempts": bucket["doc_count"]}
                for bucket in aggs.get("top_failed_usernames", {}).get("usernames", {}).get("buckets", [])
            ],
            "http_methods": [
                {"method": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get("http_methods", {}).get("buckets", [])
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ES] Error getting stats: {e}")
        return {}
