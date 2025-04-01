#!/bin/bash

# Step 1: Ensure the .env file exists
if [ ! -f .env ]; then
    echo "OPENAI_API_KEY=your-openai-api-key" > .env
    echo "Created .env file. Please replace 'your-openai-api-key' with your actual API key."
    exit 1
fi

# Step 2: Run the FastAPI application
uvicorn app.main:app --reload