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
    
async def get_hourly_activity(days: int = 7, interval: str = 'hour') -> Dict[str, Any]:
    """
    Get activity trends with flexible time intervals.
    Used for activity trend visualization.
    
    Args:
        days: Number of days to fetch (default: 7)
        interval: Aggregation interval - 'hour', 'day', or 'week' (default: 'hour')
        
    Returns:
        Dictionary with activity data grouped by the specified interval
    """
    if not elasticsearch_client.client:
        return {}
    
    try:
        # Get data for the last N days
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Configure aggregation based on interval
        if interval == 'hour':
            # Hourly data grouped by day
            query = {
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": start_time.isoformat(),
                            "lte": end_time.isoformat()
                        }
                    }
                },
                "aggs": {
                    "activity_by_day": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "day",
                            "time_zone": "America/Los_Angeles",
                            "min_doc_count": 0
                        },
                        "aggs": {
                            "hourly_activity": {
                                "date_histogram": {
                                    "field": "timestamp",
                                    "fixed_interval": "1h",
                                    "time_zone": "America/Los_Angeles",
                                    "min_doc_count": 0
                                },
                                "aggs": {
                                    "request_count": {
                                        "value_count": {
                                            "field": "timestamp"
                                        }
                                    },
                                    "failed_count": {
                                        "filter": {
                                            "term": {"response_success": False}
                                        }
                                    },
                                    "avg_response_time": {
                                        "avg": {
                                            "field": "processing_time_ms"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "size": 0
            }
        elif interval == 'day':
            # Daily aggregation for week view
            query = {
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": start_time.isoformat(),
                            "lte": end_time.isoformat()
                        }
                    }
                },
                "aggs": {
                    "daily_activity": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "day",
                            "time_zone": "America/Los_Angeles",
                            "min_doc_count": 0
                        },
                        "aggs": {
                            "request_count": {
                                "value_count": {
                                    "field": "timestamp"
                                }
                            },
                            "failed_count": {
                                "filter": {
                                    "term": {"response_success": False}
                                }
                            },
                            "avg_response_time": {
                                "avg": {
                                    "field": "processing_time_ms"
                                }
                            }
                        }
                    }
                },
                "size": 0
            }
        else:  # week or month
            # Weekly aggregation for month view
            query = {
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": start_time.isoformat(),
                            "lte": end_time.isoformat()
                        }
                    }
                },
                "aggs": {
                    "weekly_activity": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "week",
                            "time_zone": "America/Los_Angeles",
                            "min_doc_count": 0
                        },
                        "aggs": {
                            "request_count": {
                                "value_count": {
                                    "field": "timestamp"
                                }
                            },
                            "failed_count": {
                                "filter": {
                                    "term": {"response_success": False}
                                }
                            },
                            "avg_response_time": {
                                "avg": {
                                    "field": "processing_time_ms"
                                }
                            }
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
        
        # Format response based on interval
        if interval == 'hour':
            day_buckets = aggs.get("activity_by_day", {}).get("buckets", [])
            
            # Format data for frontend
            activity_data = []
            for day_bucket in day_buckets:
                day_timestamp = day_bucket["key_as_string"]
                day_date = datetime.fromisoformat(day_timestamp.replace('Z', '+00:00'))
                
                hourly_buckets = day_bucket.get("hourly_activity", {}).get("buckets", [])
                hourly_data = []
                
                for hour_bucket in hourly_buckets:
                    hour_timestamp = hour_bucket["key_as_string"]
                    hour = datetime.fromisoformat(hour_timestamp.replace('Z', '+00:00')).hour
                    
                    avg_time = hour_bucket.get("avg_response_time", {}).get("value")
                    avg_response_time = round(avg_time, 2) if avg_time is not None else 0.0
                    
                    hourly_data.append({
                        "hour": hour,
                        "requests": hour_bucket.get("request_count", {}).get("value", 0),
                        "failed": hour_bucket.get("failed_count", {}).get("doc_count", 0),
                        "avg_response_time": avg_response_time
                    })
                
                activity_data.append({
                    "date": day_date.strftime("%Y-%m-%d"),
                    "day_of_week": day_date.strftime("%a"),
                    "day_of_month": day_date.day,
                    "hourly_data": hourly_data,
                    "total_requests": sum(h["requests"] for h in hourly_data)
                })
            
            logger.info(f"[ES] Fetched hourly activity data for {len(activity_data)} days")
            return {
                "interval": "hour",
                "days": activity_data,
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat()
            }
            
        elif interval == 'day':
            daily_buckets = aggs.get("daily_activity", {}).get("buckets", [])
            
            daily_data = []
            for bucket in daily_buckets:
                bucket_date = datetime.fromisoformat(bucket["key_as_string"].replace('Z', '+00:00'))
                
                avg_time = bucket.get("avg_response_time", {}).get("value")
                avg_response_time = round(avg_time, 2) if avg_time is not None else 0.0
                
                daily_data.append({
                    "date": bucket_date.strftime("%Y-%m-%d"),
                    "day_of_week": bucket_date.strftime("%a"),
                    "day_of_month": bucket_date.day,
                    "requests": bucket.get("request_count", {}).get("value", 0),
                    "failed": bucket.get("failed_count", {}).get("doc_count", 0),
                    "avg_response_time": avg_response_time
                })
            
            logger.info(f"[ES] Fetched daily activity data for {len(daily_data)} days")
            return {
                "interval": "day",
                "data": daily_data,
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat()
            }
            
        else:  # week
            weekly_buckets = aggs.get("weekly_activity", {}).get("buckets", [])
            
            weekly_data = []
            for bucket in weekly_buckets:
                bucket_date = datetime.fromisoformat(bucket["key_as_string"].replace('Z', '+00:00'))
                
                avg_time = bucket.get("avg_response_time", {}).get("value")
                avg_response_time = round(avg_time, 2) if avg_time is not None else 0.0
                
                weekly_data.append({
                    "week_start": bucket_date.strftime("%Y-%m-%d"),
                    "week_number": bucket_date.isocalendar()[1],
                    "requests": bucket.get("request_count", {}).get("value", 0),
                    "failed": bucket.get("failed_count", {}).get("doc_count", 0),
                    "avg_response_time": avg_response_time
                })
            
            logger.info(f"[ES] Fetched weekly activity data for {len(weekly_data)} weeks")
            return {
                "interval": "week",
                "data": weekly_data,
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"[ES] Error getting activity data: {e}")
        return {}


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
