#!/bin/bash

# Default Environment Variables
REDACTOR_TYPE="pattern"
REDACTION_STYLE="mask"
LLM_MODEL="llama3.2:3b"
OLLAMA_URL="http://localhost:11434"

# Parse Command Line Arguments for Redactor Type
while getopts "r:s:m:" option; do
    case $option in
        r) REDACTOR_TYPE=$OPTARG ;;  # Set redactor type (pattern or llm)
        s) REDACTION_STYLE=$OPTARG ;; # Set redaction style
        m) LLM_MODEL=$OPTARG ;;      # Set LLM model name
       \?) 
           echo "Invalid option: -$OPTARG" >&2
           echo "Usage: $0 [-r redactor_type] [-s redaction_style] [-m llm_model]"
           exit 1 
           ;;
    esac
done

echo "Starting Privacy-Preserving AI Proxy..."
echo "Redaction type: $REDACTOR_TYPE"
echo "Redaction style: $REDACTION_STYLE"

# Check if Ollama service is available when using LLM
if [ "$REDACTOR_TYPE" = "llm" ]; then
    echo "Checking Ollama availability..."
    curl -s "$OLLAMA_URL/api/tags" > /dev/null
    if [ $? -ne 0 ]; then
        echo "Warning: Ollama service is not available at $OLLAMA_URL"
        echo "Make sure Ollama is running before starting the application"
        exit 1
    else
        echo "Ollama is available. Using model: $LLM_MODEL"
    fi
fi

# Set environment variables so they are accessible to the application
export REDACTOR_TYPE
export REDACTION_STYLE
export LLM_MODEL
export OLLAMA_URL

# Start the FastAPI application using Poetry
poetry run uvicorn app.main:app --reload