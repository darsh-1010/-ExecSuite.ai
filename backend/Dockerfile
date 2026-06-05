# Base Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0
ENV SKIP_BROWSER=true

# Set working directory
WORKDIR /app/backend

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# Create workspace directory
RUN mkdir -p /app/workspace

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "run.py"]
