#!/usr/bin/env python3
"""
Simple RAG Pipeline for Semantic History
- Store flagged items as embeddings
- Query for similar items
- Persistent local storage
"""

import asyncio
import chromadb
from typing import List, Dict, Any
import uuid
from datetime import datetime

class SimpleRAG:
    def __init__(self, db_path: str = "./chroma_db"):
        """Initialize the simple RAG system."""
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="semantic_history",
            metadata={"description": "Semantic history of flagged items"}
        )
    
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
        if metadata is None:
            metadata = {}
        
        # Generate unique ID
        item_id = str(uuid.uuid4())
        
        # Store structured data in metadata (not embedded)
        metadata.update({
            "user": user,
            "ip": ip,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        
        # Only embed the reasoning text (not user, IP, severity)
        await asyncio.to_thread(
            self.collection.add,
            ids=[item_id],
            documents=[reasoning],  # Only reasoning gets vectorized
            metadatas=[metadata]
        )
        
        return item_id
    
    async def query_items(self, query_text: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Query for similar items in the semantic history.
        
        Args:
            query_text: The query string
            k: Number of top results to return
            
        Returns:
            List of similar items with scores
        """
        # Query ChromaDB (async wrapper)
        results = await asyncio.to_thread(
            self.collection.query,
            query_texts=[query_text],
            n_results=k
        )
        
        # Format results
        items = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                item = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "score": float(results["distances"][0][i]) if results["distances"] else 0.0,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                }
                items.append(item)
        
        return items
    
    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items in the collection."""
        results = await asyncio.to_thread(
            self.collection.get
        )
        
        items = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                item = {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                }
                items.append(item)
        
        return items
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete an item by ID."""
        try:
            await asyncio.to_thread(
                self.collection.delete,
                ids=[item_id]
            )
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = await asyncio.to_thread(self.collection.count)
        return {
            "total_items": count,
            "collection_name": self.collection.name
        }
    
    async def clear_all(self) -> bool:
        """Clear all items from the collection."""
        try:
            # Get all IDs first
            all_items = await asyncio.to_thread(self.collection.get)
            if all_items["ids"]:
                await asyncio.to_thread(
                    self.collection.delete,
                    ids=all_items["ids"]
                )
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