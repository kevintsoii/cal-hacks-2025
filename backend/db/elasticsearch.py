from elasticsearch import AsyncElasticsearch
from typing import Optional, Dict, Any, List
import os


class ElasticsearchClient:
    """
    Async Elasticsearch client wrapper with basic operations.
    """
    
    def __init__(self):
        """Initialize Elasticsearch connection."""
        es_endpoint = os.getenv("ELASTICSEARCH_ENDPOINT")
        es_api_key = os.getenv("ELASTICSEARCH_API_KEY")
        
        if not es_endpoint or not es_api_key:
            raise ValueError("ELASTICSEARCH_ENDPOINT and ELASTICSEARCH_API_KEY must be set in environment variables")
        
        self.client = AsyncElasticsearch(
            es_endpoint,
            api_key=es_api_key,
            verify_certs=True,
            request_timeout=30
        )
    
    async def ping(self) -> bool:
        """
        Ping Elasticsearch to check connection.
        """
        return await self.client.ping()
    
    async def create_index(self, index_name: str, mappings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create an index in Elasticsearch.
        """
        if await self.client.indices.exists(index=index_name):
            print(f"Index {index_name} already exists")
            return True
        
        body = {}
        if mappings:
            body["mappings"] = mappings
        
        await self.client.indices.create(index=index_name, body=body)
        return True
    
    async def index_document(self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> Optional[str]:
        """
        Index a document in Elasticsearch.
        """
        if doc_id:
            result = await self.client.index(index=index_name, id=doc_id, document=document)
        else:
            result = await self.client.index(index=index_name, document=document)
        return result['_id']
    
    async def search(self, index_name: str, query: Dict[str, Any], size: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents in Elasticsearch.
        """
        result = await self.client.search(index=index_name, query=query, size=size)
        return [hit['_source'] for hit in result['hits']['hits']]
    
    async def close(self):
        """Close the Elasticsearch connection."""
        await self.client.close()


# Global Elasticsearch client instance
elasticsearch_client = ElasticsearchClient()