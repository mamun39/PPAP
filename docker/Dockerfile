FROM python:3.10-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy dependency file first for better caching
COPY requirements.txt ./

# Install pip requirements
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser --uid 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Use Uvicorn directly for better FastAPI performance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]