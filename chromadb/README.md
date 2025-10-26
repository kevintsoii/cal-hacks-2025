# ChromaDB Service

Separate microservice for vector embeddings and semantic search.

## Architecture

This is a standalone Python service running in its own Docker container with its own dependencies. It provides an HTTP API for storing and querying security incidents with vector embeddings.

## Why Separate Service?

- **Dependency isolation**: ChromaDB requires protobuf 6.x, while the backend (cosmpy) requires protobuf <6.0
- **Independent scaling**: Can scale ChromaDB separately from backend
- **Cleaner architecture**: Microservices pattern

## ChromaDB Commands
### 1. Check stats (how many items stored)
curl http://localhost:9000/stats

### 2. View all stored mitigations
curl http://localhost:9000/all | jq

### 3. Search for similar threats (semantic search)
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "brute force login", "k": 5}' | jq

### 4. Clear all data (if needed)
curl -X DELETE http://localhost:9000/clear

## API Endpoints

### `GET /`
Health check with collection stats

### `POST /add`
Add a new item with vector embeddings
```json
{
  "reasoning": "Threat description",
  "user": "username",
  "ip": "192.168.1.1",
  "severity": 3,
  "metadata": {}
}
```

### `POST /query`
Query for similar items using semantic search
```json
{
  "query_text": "brute force login attack",
  "k": 5
}
```

### `GET /all`
Get all items in the collection

### `GET /stats`
Get collection statistics

### `DELETE /clear`
Clear all items from the collection

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
```

Service runs on http://localhost:9000

## Docker

Built and run via docker-compose from project root.

