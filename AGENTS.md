# Project Name

## Architecture
This project is an AI-powered API security middleware that uses AI agents & LLMs to detect and automatically mitigate malicious API behavior (brute-force logins, scrapiing).
- FastAPI middleware covers all API routes
 - 1st, do a quick check on Redis for any active mitigations and return early with an error if one exists
  - mitigations: nothing > small 100-500ms request delay > captcha > temporary block > full ban
 - 2nd, allows the API request to process
 - 3rd, adds API request details to an internal non-blocking queue + to elasticsearch
 - The queue asynchronously feeds to the AI agent pipeline every 5s / at 100 requests
- Fetch.AI agents handle all detection using Groq as the LLM provider + tool calling + RAG memory
 - Orchestrator Agent -> splits the batch of requests to the specialized agent for the request type
 - Specialized Agents (Auth/Search/General) -> Analyze the requests, uses tool calling to access elasticsearch logs, and decide which Users/IPs to apply mitigations to
 - Calibration Agent -> uses RAG + ChromaDB on past mitigations to amplify or downgrade the mitigation suggested by specialized agent.
  - saves the newly calibrated mitigation to ChromaDB with semantic reasoning for future reference
  - Applies the mitigation to Redis
- Human Inputs (wheter an auto-mitigation was good or bad) will be provided to the Calibration Agent for future use

## Frontend
- Use TypeScript
- Use Radix UI for icons
- Use TailwindCSS for all CSS changes
- Use shadcn for all UI components
  - Download all components directly using npx shadcn@latest add <component-name>
- Do not npm run dev to test changes

## General
- When installing new packages, use npm install or pip install rather than an arbitrary package version directly in the packages file