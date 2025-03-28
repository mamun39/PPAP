import os
import requests
import logging
from fastapi import FastAPI, Request
from app.services.privacy import scrub_pii  # Import the scrub_pii function from your app's privacy module
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Initialize the FastAPI app
app = FastAPI()

@app.post("/chat")
async def chat_with_proxy(request: Request):
    """
    Intercepts request, scrubs PII, and forwards to OpenAI API.
    """
    # Get the message from the user query
    data = await request.json()
    user_query = data.get("message", "")

    # Scrub sensitive info from the user input using the scrub_pii function
    sanitized_query = scrub_pii(user_query)

    logging.info("Sanitized Query: %s", sanitized_query)

    # Prepare the request to OpenAI API
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4",  # You can replace with another model such as "gpt-3.5-turbo"
        "messages": [{"role": "user", "content": sanitized_query}],
    }

    # Make the request to the OpenAI API
    try:
        response = requests.post(OPENAI_API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        openai_response = response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

    # Return the response from OpenAI API back to the user
    return openai_response