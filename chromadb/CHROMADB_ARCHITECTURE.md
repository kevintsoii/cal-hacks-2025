# ChromaDB Microservice Architecture

## Overview

ChromaDB runs as a **separate Python microservice** with its own Docker container, dependencies, and virtual environment. This solves the protobuf dependency conflict between ChromaDB and cosmpy.

## Project Structure

```
cal-hacks-2025/
├── backend/              # Backend service (Python 3.11 + cosmpy + protobuf <6)
│   ├── agents/
│   ├── rag/
│   │   └── simple_rag.py    # HTTP client to ChromaDB service
│   ├── requirements.txt     # NO chromadb dependency
│   └── Dockerfile
│
├── chromadb/             # NEW: ChromaDB service (Python 3.11 + chromadb + protobuf 6.x)
│   ├── main.py              # FastAPI server exposing ChromaDB API
│   ├── requirements.txt     # chromadb==1.2.1 with protobuf 6.x
│   ├── Dockerfile
│   └── README.md
│
├── frontend/             # React frontend
└── docker-compose.yml    # Orchestrates all services
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Backend         │      │  ChromaDB        │            │
│  │  Container       │      │  Container       │            │
│  │                  │      │                  │            │
│  │  Python 3.11     │──────│  Python 3.11     │            │
│  │  cosmpy          │ HTTP │  chromadb 1.2.1  │            │
│  │  protobuf 4.x    │      │  protobuf 6.x    │            │
│  │                  │      │                  │            │
│  │  simple_rag.py   │      │  FastAPI Server  │            │
│  │  (HTTP client)   │      │  (Vector Store)  │            │
│  └──────────────────┘      └──────────────────┘            │
│                                      │                       │
│                                      ▼                       │
│                             ┌──────────────────┐            │
│                             │  chromadb-data   │            │
│                             │  Volume          │            │
│                             │  (Persistent)    │            │
│                             └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Communication Flow

1. **Calibration Agent** (backend) calls `rag.add_item()` or `rag.query_items()`
2. **simple_rag.py** makes HTTP POST/GET request to ChromaDB service
3. **ChromaDB Service** (chromadb/main.py) receives request
4. **ChromaDB** creates vector embeddings and stores/queries data
5. **Response** returned to backend as JSON

## Benefits

### ✅ Dependency Isolation
- Backend: cosmpy requires protobuf <6.0 ✅
- ChromaDB: chromadb requires protobuf 6.x ✅
- No conflicts! Each service has its own Python environment

### ✅ Microservices Architecture
- Independent deployment and scaling
- Can update ChromaDB version without touching backend
- Cleaner separation of concerns

### ✅ Persistent Storage
- ChromaDB data stored in Docker volume
- Survives container restarts
- Can backup/restore independently

### ✅ HTTP API
- Language agnostic - could call from any service
- Easy to test independently
- Standard REST endpoints

## Environment Variables

### Backend
```bash
CHROMADB_URL=http://chromadb:9000  # Set in docker-compose.yml
```

### ChromaDB Service
No special env vars needed - stores data in `/chroma_data` volume

## Ports

- **Backend**: 8000-8005
- **ChromaDB**: 9000
- **Redis**: 6379
- **Frontend**: 5173

## Running

```bash
# Build and start all services
docker compose up --build

# ChromaDB will start on port 9000
# Backend will connect via CHROMADB_URL environment variable
```

## Testing ChromaDB Service Directly

```bash
# Health check
curl http://localhost:9000/

# Add an item
curl -X POST http://localhost:9000/add \
  -H "Content-Type: application/json" \
  -d '{
    "reasoning": "Brute force login attempt detected",
    "user": "attacker123",
    "ip": "192.168.1.100",
    "severity": 5,
    "metadata": {}
  }'

# Query similar items
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "login attack",
    "k": 5
  }'

# Get stats
curl http://localhost:9000/stats
```

## Data Persistence

ChromaDB data is stored in a Docker volume:
```yaml
volumes:
  chromadb-data:  # Persists across container restarts
```

To clear all data:
```bash
docker volume rm cal-hacks-2025_chromadb-data
```

## Future Enhancements

- Add authentication to ChromaDB API
- Implement rate limiting
- Add monitoring/metrics endpoints
- Support multiple collections
- Add backup/restore endpoints

