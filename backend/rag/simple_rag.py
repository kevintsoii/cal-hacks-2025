#!/usr/bin/env python3
"""
Simple RAG Pipeline for Semantic History
- Store flagged items as embeddings
- Query for similar items
- Connects to ChromaDB service via HTTP
"""

import asyncio
import httpx
from typing import List, Dict, Any
import os
from datetime import datetime

class SimpleRAG:
    def __init__(self, chromadb_url: str = None):
        """Initialize the simple RAG system - connects to ChromaDB service."""
        self.chromadb_url = chromadb_url or os.getenv("CHROMADB_URL", "http://localhost:9000")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def add_item(self, reasoning: str, user: str, ip: str, severity: int, metadata: Dict[str, Any] = None) -> str:
        """
        Add a new security incident to the semantic history.
        
        Args:
            reasoning: The reasoning text to embed (what gets vectorized)
            user: Username (stored in metadata only)
            ip: IP address (stored in metadata only) 
            severity: Severity score 1-5 (stored in metadata only)
            metadata: Optional additional metadata
            
        Returns:
            str: The ID of the added item
        """
        payload = {
            "reasoning": reasoning,
            "user": user,
            "ip": ip,
            "severity": severity,
            "metadata": metadata
        }
        
        response = await self.client.post(
            f"{self.chromadb_url}/add",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        return result["id"]
    
    async def query_items(self, query_text: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Query for similar items in the semantic history.
        
        Args:
            query_text: The query string
            k: Number of top results to return
            
        Returns:
            List of similar items with scores
        """
        payload = {
            "query_text": query_text,
            "k": k
        }
        
        response = await self.client.post(
            f"{self.chromadb_url}/query",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        return result["items"]
    
    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items in the collection."""
        response = await self.client.get(f"{self.chromadb_url}/all")
        response.raise_for_status()
        result = response.json()
        return result["items"]
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete an item by ID."""
        try:
            # Not implemented in service yet, would need to add endpoint
            return False
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        response = await self.client.get(f"{self.chromadb_url}/stats")
        response.raise_for_status()
        result = response.json()
        return {
            "total_items": result["total_items"],
            "collection_name": result["collection_name"]
        }
    
    async def clear_all(self) -> bool:
        """Clear all items from the collection."""
        try:
            response = await self.client.delete(f"{self.chromadb_url}/clear")
            response.raise_for_status()
            return True
        except Exception:
            return False

# Global instance
rag = SimpleRAG()

# Convenience functions
async def add_security_incident(reasoning: str, user: str, ip: str, severity: int, metadata: Dict[str, Any] = None) -> str:
    """Add a security incident to the semantic history."""
    return await rag.add_item(reasoning, user, ip, severity, metadata)

async def add_incident_from_csv(user: str, ip: str, severity: int, reasoning: str) -> str:
    """Add incident from CSV format: user,ip,severity,reasoning"""
    return await rag.add_item(reasoning, user, ip, severity)

async def query_similar_items(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Query for similar flagged items."""
    return await rag.query_items(query, k)

async def get_all_flagged_items() -> List[Dict[str, Any]]:
    """Get all flagged items."""
    return await rag.get_all_items()

async def get_rag_stats() -> Dict[str, Any]:
    """Get RAG system statistics."""
    return await rag.get_stats()

async def clear_all_incidents() -> bool:
    """Clear all incidents from the database."""
    return await rag.clear_all()