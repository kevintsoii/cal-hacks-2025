# AI-Powered API Security Middleware

An intelligent API security solution that leverages AI agents and Large Language Models to automatically detect and mitigate malicious API behavior in real-time, including brute-force login attempts, web scraping, and other suspicious activities.

## 🌟 Features

- **Real-time Threat Detection**: Monitors all API traffic and identifies suspicious patterns using AI agents
- **Intelligent Mitigation**: Progressive mitigation strategy from request delays to full bans
- **Multi-Agent Architecture**: Specialized AI agents for different API endpoint types (Auth, Search, General)
- **Adaptive Learning**: RAG-based calibration system that learns from past mitigations
- **Human-in-the-Loop**: Incorporates human feedback to improve detection accuracy
- **Live Dashboard**: Real-time monitoring interface with metrics, threat analysis, and mitigation controls
- **Elasticsearch Integration**: Comprehensive logging and querying of API traffic
- **WebSocket Updates**: Live streaming of security events to the frontend

## 🏗️ Architecture

### Request Flow

```
API Request → FastAPI Middleware
    ↓
1. Redis Check (Active Mitigations)
    ↓
2. Process API Request
    ↓
3. Log to Agent Pipeline Queue + Elasticsearch
    ↓
4. Async Agent Pipeline (every 5s / 100 requests)
    ↓
Orchestrator Agent → Specialized Agents → Calibration Agent (+ RAG memory) → Redis (Apply Mitigation)
```

### Mitigation Levels

Progressive mitigation strategy based on threat severity:
1. **None**: Normal operation
2. **Small Delay**: 100-500ms request delay
3. **Captcha**: reCAPTCHA challenge
4. **Temporary Block**: Time-limited access restriction
5. **Full Ban**: Permanent IP/user blocking

### AI Agent System

**Orchestrator Agent**
- Receives batched API requests
- Routes requests to specialized agents based on endpoint type
- Coordinates the detection pipeline

**Specialized Agents**
- **Auth Agent**: Analyzes authentication endpoints (login, signup, password reset)
- **Search Agent**: Monitors search and query endpoints
- **General Agent**: Handles all other API traffic
- Uses tool calling to query Elasticsearch logs
- Determines appropriate mitigations for suspicious IPs/users

**Calibration Agent**
- Uses RAG + ChromaDB to access historical mitigation data
- Amplifies or downgrades suggested mitigations based on past outcomes
- Stores calibrated decisions with semantic reasoning
- Learns from human feedback

**Support Agents**
- **Chatbot Agent**: Interactive security assistant for the dashboard
- **ESQL Query Agent**: Natural language to Elasticsearch query translation

**Live Feedback**
- Configurable Agent Prompts through our dashboard
- Calibration feedback by a human in the loop adds to RAG for extra context

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Fetch.AI (uAgents)**: Multi-agent framework for distributed AI agents
- **Groq**: LLM provider for agent intelligence
- **Redis**: Fast caching and mitigation state management
- **Elasticsearch**: Efficient logging and analytics
- **ChromaDB**: Vector database for semantic search and RAG-based learning
- **Python 3.11+**: Core language

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **TailwindCSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality UI components
- **Radix UI**: Accessible component primitives
- **WebSocket**: Real-time updates

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Elasticsearch instance (cloud)
- Groq account
- ReCAPTCHA account

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# LLM Provider
GROQ_API_KEY=your_groq_api_key
ELASTICSEARCH_ENDPOINT=your_elasticsearch_url
ELASTICSEARCH_API_KEY=your_elasticsearch_api_key
RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key
```

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd cal-hacks-2025
```

2. **Start all services with Docker Compose**
```bash
docker-compose up --build
```

This will start:
- Backend API (port 8000)
- All AI agents (ports 8001-8007)
- Frontend (port 5173)
- Redis (port 6379)
- ChromaDB (port 9000)

3. **Access the application**
- Frontend Dashboard: http://localhost:5173
- Backend API: http://localhost:8000

## 📊 Usage

### Dashboard

The web dashboard provides:
- **Metrics Overview**: Real-time statistics on requests, threats detected, and active mitigations
- **Activity Chart**: Visual representation of traffic patterns
- **Detection Log**: Live stream of API requests and security events
- **Threat Analysis**: Detailed breakdown of detected threats
- **Active Mitigations**: Current mitigation rules and controls
- **Agent Rules Management**: Configure detection rules for specialized agents
- **Security Chat**: Interactive AI assistant for security queries
- **Test Suite**: Built-in traffic generation for testing

### API Integration

To protect your API with this middleware, wrap your FastAPI application:

```python
from fastapi import FastAPI
from middleware.middleware import SecurityMiddleware

app = FastAPI()
app.add_middleware(SecurityMiddleware)

@app.get("/api/protected")
async def protected_endpoint():
    return {"message": "This endpoint is protected"}
```

## 🤖 Fetch.AI Agent Info

- Orchestrator Agent
    - agent1q0a3vglkxzlaqdgysyl6l7tzfpz5awc2amy2ek50mje0ngqyhrr9k8pjsw5
    - https://agentverse.ai/agents/details/agent1q0a3vglkxzlaqdgysyl6l7tzfpz5awc2amy2ek50mje0ngqyhrr9k8pjsw5/profile

- Auth API Specialist Agent 
    - agent1q054vfyk2qqnqwsrw804avurynvwkk9vdjcqu9q0at52zlaa5urxv0md3sk
    - https://agentverse.ai/agents/details/agent1q054vfyk2qqnqwsrw804avurynvwkk9vdjcqu9q0at52zlaa5urxv0md3sk/profile

- Search API Specialist Agent
    - agent1qtpatn2rged8wspghgl8sex9e05s78fvmh84pnyf5ghn6ue0t6vkjvp03mg
    - https://agentverse.ai/agents/details/agent1qtpatn2rged8wspghgl8sex9e05s78fvmh84pnyf5ghn6ue0t6vkjvp03mg/profile

- General API Specialist Agent
    - agent1q2ackrd978swlwajsswm4kjr9cszhc9rxgnuyy7rv9jzh4v3jta25vzv668
    - https://agentverse.ai/agents/details/agent1q2ackrd978swlwajsswm4kjr9cszhc9rxgnuyy7rv9jzh4v3jta25vzv668/profile

- Mitigation Calibration Agent
    - agent1qgnl0fly845g2zlx904lsgwygl4vl7jygcx7xyxf82zu95g26mgmy0dk9rt
    - https://agentverse.ai/agents/details/agent1qgnl0fly845g2zlx904lsgwygl4vl7jygcx7xyxf82zu95g26mgmy0dk9rt/profile

- Chatbot Agent
    - agent1qw7m6gyh3swk38gw3zkc86sa2wrjqrcykvpzjeeqrxv8k4fgskzpzac6kk5
    - https://agentverse.ai/agents/details/agent1qw7m6gyh3swk38gw3zkc86sa2wrjqrcykvpzjeeqrxv8k4fgskzpzac6kk5/profile

- ESQL Query Agent
    - agent1qwxyzc74yr92wstx0g7q4fmvzezev08495m5jq0yl9pwz05ur5gly5t4kuy
    - https://agentverse.ai/agents/details/agent1qwxyzc74yr92wstx0g7q4fmvzezev08495m5jq0yl9pwz05ur5gly5t4kuy/profile

### Agent Communication

Agents communicate via Fetch.AI's uAgents protocol:
1. Orchestrator receives request batches
2. Messages routed to specialized agents
3. Specialized agents analyze and respond with threat assessments
4. Calibration agent refines mitigation levels
5. Mitigations applied to Redis

### Agent Rules

Each specialized agent follows rules defined in `backend/agent_rules/`:
- `auth_agent_rules.txt`: Authentication endpoint patterns
- `search_agent_rules.txt`: Search behavior indicators
- `general_agent_rules.txt`: General traffic anomalies

Rules can be updated through the dashboard's Agent Rules page.
