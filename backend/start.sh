#!/bin/bash

# Start the Auth agent in the background
echo "Starting Auth Agent on port 8002..."
python agents/auth_agent.py &
AUTH_PID=$!

# Start the Search agent in the background
echo "Starting Search Agent on port 8003..."
python agents/search_agent.py &
SEARCH_PID=$!

# Start the General agent in the background
echo "Starting General Agent on port 8004..."
python agents/general_agent.py &
GENERAL_PID=$!

# Start the Calibration agent in the background
echo "Starting Calibration Agent on port 8005..."
python agents/calibration_agent.py &
CALIBRATION_PID=$!

# Start the ESQL Query Agent in the background
echo "Starting ESQL Query Agent on port 8006..."
python esql_query_agent.py &
ESQL_PID=$!

# Start the Chatbot Agent in the background
echo "Starting Chatbot Agent on port 8007..."
python chatbot_agent.py &
CHATBOT_PID=$!

# Start the orchestrator agent in the background
echo "Starting Orchestrator Agent on port 8001..."
python agents/orchestrator_agent.py &
ORCHESTRATOR_PID=$!

# Give the agents a moment to start
sleep 3

# Start the main FastAPI application
echo "Starting FastAPI application on port 8000..."
cd /app
python main.py &
FASTAPI_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill $AUTH_PID $SEARCH_PID $GENERAL_PID $CALIBRATION_PID $ESQL_PID $CHATBOT_PID $ORCHESTRATOR_PID $FASTAPI_PID 2>/dev/null
    wait $AUTH_PID $SEARCH_PID $GENERAL_PID $CALIBRATION_PID $ESQL_PID $CHATBOT_PID $ORCHESTRATOR_PID $FASTAPI_PID 2>/dev/null
    exit 0
}

# Trap SIGTERM and SIGINT
trap shutdown SIGTERM SIGINT

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?