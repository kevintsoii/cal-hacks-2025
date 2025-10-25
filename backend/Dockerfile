# Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy fix script and apply cosmpy protobuf fix
COPY fix_cosmpy.sh .
RUN chmod +x fix_cosmpy.sh && ./fix_cosmpy.sh

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Expose ports for FastAPI and all Agents
EXPOSE 8000
EXPOSE 8001
EXPOSE 8002
EXPOSE 8003
EXPOSE 8004

# Run both applications via the startup script
CMD ["/bin/bash", "./start.sh"]