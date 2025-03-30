# Use Python 3.11 base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start services using supervisord
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $API_PORT & \
                   python monitoring_service.py & \
                   python llm_service.py"]
