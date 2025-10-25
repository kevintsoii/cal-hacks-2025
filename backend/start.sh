#!/bin/bash

# Start the orchestrator agent in the background
echo "Starting Orchestrator Agent on port 8001..."
cd /app/agents
python orchestrator_agent.py &
ORCHESTRATOR_PID=$!

# Give the orchestrator a moment to start
sleep 2

# Start the main FastAPI application
echo "Starting FastAPI application on port 8000..."
cd /app
python main.py &
FASTAPI_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $ORCHESTRATOR_PID $FASTAPI_PID 2>/dev/null
    wait $ORCHESTRATOR_PID $FASTAPI_PID 2>/dev/null
    exit 0
}

# Trap SIGTERM and SIGINT
trap shutdown SIGTERM SIGINT

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?