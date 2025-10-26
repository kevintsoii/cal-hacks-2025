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

## How we built it

Dyno is built on a sophisticated multi-layered architecture that combines three specialized databases, an intelligent AI agent pipeline, and a self-learning RAG system.

### Backend Architecture & Middleware

The core of Dyno is a **FastAPI middleware** that intercepts every API request before it reaches the application layer. The middleware follows a three-step process:

1. **Redis Check**: First, it performs a lightning-fast lookup in Redis to check if there's an active mitigation for the incoming IP or user. If found, it immediately applies the mitigation (delay, CAPTCHA, or block) without processing the request further.

2. **Request Processing**: If no mitigation exists, the request is allowed to proceed normally to the API endpoint.

3. **Asynchronous Logging**: After the request completes, the middleware non-blockingly adds the request details to both an internal queue and Elasticsearch. This ensures zero performance impact on legitimate traffic.

The internal queue batches requests and triggers the AI agent pipeline either every 5 seconds or when 100 requests accumulate — whichever comes first.

### Three-Database Architecture

We engineered Dyno to leverage three different databases, each optimized for its specific role:

**1. Redis** – The first line of defense. Redis stores active mitigations with sub-millisecond lookup times, enabling us to block attacks instantly without consulting slower databases. Every mitigation decision made by the AI agents is written here with TTLs for automatic expiration.

**2. Elasticsearch** – The comprehensive audit log. Every single API request (with metadata like IP, user, endpoint, headers, response time, status code) is indexed in Elasticsearch. This provides:
- Full-text search across all historical traffic
- Complex aggregation queries for pattern detection
- Time-series analysis of attack trends
- The data source for our AI agents to investigate suspicious behavior

**3. ChromaDB** – The memory layer. ChromaDB is a vector database that powers our RAG (Retrieval-Augmented Generation) system. It stores semantic embeddings of past mitigation decisions along with their outcomes and human feedback. When the Calibration Agent needs to make a decision, it queries ChromaDB to find similar historical cases and learns from them.

### AI Agent System

We built a **multi-agent system** using **Fetch.AI's uAgents framework**, where specialized agents collaborate to detect threats:

**Orchestrator Agent** – The traffic controller. It receives batches of API requests from the middleware queue and intelligently routes them to the appropriate specialist agent based on endpoint type (e.g., `/auth/*` → Auth Agent, `/search` → Search Agent).

**Specialized Detection Agents** – We created three specialist agents, each with domain-specific knowledge:
- **Auth Agent**: Detects brute-force login attempts, credential stuffing, account enumeration
- **Search Agent**: Identifies scraping behavior, excessive queries, suspicious search patterns  
- **General Agent**: Catches anomalies in all other endpoints

Each specialist agent receives custom rules (loaded from `agent_rules/` directory) that define what patterns to look for. The agents use **Groq's LLM API** (specifically Llama models) to analyze batches of requests and use **tool calling** to query Elasticsearch for historical context about IPs or users. After analysis, they suggest a mitigation level for suspicious actors.

**Calibration Agent** – The learning layer. This agent takes the raw mitigation suggestions from specialists and refines them using historical knowledge:
- Queries ChromaDB using RAG to find semantically similar past incidents
- Amplifies or downgrades the mitigation based on what worked before
- Saves the final decision back to ChromaDB with reasoning for future reference
- Incorporates human feedback from the dashboard to continuously improve

The calibrated mitigation is then written to Redis, completing the loop.

### RAG + Feedback System

The RAG (Retrieval-Augmented Generation) system is what makes Dyno adaptive:

1. **Historical Storage**: Every mitigation decision is embedded and stored in ChromaDB along with:
   - The request patterns that triggered it
   - The mitigation level applied
   - Whether it was effective
   - Any human feedback (thumbs up/down from the dashboard)

2. **Semantic Retrieval**: When the Calibration Agent evaluates a new threat, it performs a semantic search in ChromaDB to find similar past cases — not just exact matches, but situations with similar characteristics.

3. **Context-Aware Decisions**: The agent uses retrieved examples as context in its LLM prompt, asking: "Given these similar past cases, should I increase or decrease the suggested mitigation?"

4. **Human-in-the-Loop**: Security engineers can mark mitigations as correct or incorrect through the dashboard. This feedback is immediately incorporated into ChromaDB, so the system learns from mistakes in real-time.

5. **Rule Customization**: The dashboard also allows live editing of agent rules, which are hot-reloaded into the agents without requiring restarts.

### Frontend & Real-Time Communication

The dashboard is built with **React + TypeScript** using **shadcn/ui** components and **TailwindCSS** for styling. It connects to the backend via **WebSocket** for real-time streaming of:
- Live API request logs
- Threat detection alerts
- Mitigation applications
- Agent decision explanations

We also implemented a security **chatbot agent** that lets users query the system in natural language (e.g., "Show me all blocked IPs from the last hour") by translating queries to Elasticsearch DSL.

### Infrastructure

Everything is containerized with **Docker** and orchestrated via **docker-compose**, making deployment a single command. The entire stack — FastAPI backend, 6 AI agents, Redis, ChromaDB, and the React frontend — spins up together with automatic service discovery.

## What's next

- **Multi-Framework Support**: Extend beyond FastAPI to support Express.js, Django, Rails, and other popular web frameworks
- **Behavioral Fingerprinting**: Build user behavior profiles over time to detect subtle account takeovers and anomalous sessions
- **Edge Deployment**: Deploy lightweight detection agents at CDN edge locations for sub-10ms global mitigation response times
- **Threat Intelligence Integration**: Automatically incorporate external threat feeds (malicious IPs, compromised credentials) into agent decisions
- **Enterprise Multi-Tenancy**: Enable multiple organizations to use shared Dyno infrastructure with isolated data and configurations
