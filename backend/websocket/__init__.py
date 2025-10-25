"""
WebSocket package for real-time Elasticsearch updates.
"""

from .connection_manager import manager, ConnectionManager
from .elasticsearch_poller import get_recent_logs, get_recent_stats

__all__ = ['manager', 'ConnectionManager', 'get_recent_logs', 'get_recent_stats']