# Base Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0
ENV SKIP_BROWSER=true

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend, frontend, and create workspace directory
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
RUN mkdir -p /app/workspace

# Set workdir to backend to run
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "run.py"]
