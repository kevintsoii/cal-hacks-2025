FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies (ChromaDB with protobuf 6.x - no conflict!)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Create data directory for ChromaDB persistent storage
RUN mkdir -p /chroma_data

# Expose port
EXPOSE 9000

# Run the FastAPI server
CMD ["python", "main.py"]

