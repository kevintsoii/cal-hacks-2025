#!/usr/bin/env python3
"""
ChromaDB Service - Separate microservice for vector embeddings
Provides HTTP API for storing and querying semantic data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChromaDB Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize ChromaDB with persistent storage
client = chromadb.PersistentClient(
    path="/chroma_data",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Get or create collection
collection = client.get_or_create_collection(
    name="semantic_history",
    metadata={"description": "Semantic history of security incidents"}
)


class AddItemRequest(BaseModel):
    reasoning: str
    user: str
    ip: str
    severity: int
    metadata: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    query_text: str
    k: int = 5


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "ChromaDB Service",
        "status": "healthy",
        "collection": collection.name,
        "count": collection.count()
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        count = collection.count()
        return {
            "status": "healthy",
            "collection_name": collection.name,
            "total_items": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add")
async def add_item(request: AddItemRequest):
    """Add a new item to the collection with vector embeddings."""
    try:
        from datetime import datetime
        import uuid
        
        logger.info(f"Received add request: user={request.user}, ip={request.ip}, severity={request.severity}")
        logger.info(f"Metadata: {request.metadata}")
        
        # Generate unique ID
        item_id = str(uuid.uuid4())
        
        # Prepare metadata - ensure all values are JSON serializable
        metadata = request.metadata or {}
        
        # ChromaDB metadata must be strings, ints, floats, or bools
        # Convert everything to appropriate types
        clean_metadata = {}
        for key, value in metadata.items():
            if value is None:
                continue  # Skip None values
            elif isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            else:
                clean_metadata[key] = str(value)  # Convert to string
        
        # Add standard fields
        clean_metadata.update({
            "user": str(request.user),
            "ip": str(request.ip),
            "severity": int(request.severity),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Clean metadata: {clean_metadata}")
        
        # Add to ChromaDB (automatically creates embeddings)
        collection.add(
            ids=[item_id],
            documents=[request.reasoning],
            metadatas=[clean_metadata]
        )
        
        logger.info(f"Successfully added item {item_id}")
        
        return {
            "success": True,
            "id": item_id,
            "message": "Item added successfully with vector embeddings"
        }
    except Exception as e:
        logger.error(f"Error adding item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding item: {str(e)}")


@app.post("/query")
async def query_items(request: QueryRequest):
    """Query for similar items using semantic search."""
    try:
        # Query ChromaDB with vector similarity
        results = collection.query(
            query_texts=[request.query_text],
            n_results=request.k
        )
        
        # Format results
        items = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                item = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "score": float(results["distances"][0][i]) if results.get("distances") else 0.0,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {}
                }
                items.append(item)
        
        return {
            "success": True,
            "count": len(items),
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying items: {str(e)}")


@app.get("/all")
async def get_all_items():
    """Get all items in the collection."""
    try:
        results = collection.get()
        
        items = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                item = {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                }
                items.append(item)
        
        return {
            "success": True,
            "count": len(items),
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting items: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get collection statistics."""
    try:
        count = collection.count()
        return {
            "success": True,
            "total_items": count,
            "collection_name": collection.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.delete("/clear")
async def clear_all():
    """Clear all items from the collection."""
    try:
        # Get all IDs and delete them
        all_items = collection.get()
        if all_items["ids"]:
            collection.delete(ids=all_items["ids"])
        
        return {
            "success": True,
            "message": "All items cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing items: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)

