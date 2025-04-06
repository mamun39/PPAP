import os
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv
from app.services.privacy import PiiRedactor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

app = FastAPI(title="Privacy-Preserving AI Proxy (PPAP)", version="1.0.0")

class ChatRequest(BaseModel):
    message: str = Field(..., 
        example="What's the weather in New York?",
        min_length=1,
        max_length=2000,
        description="User message to be processed")

async def get_redactor() -> PiiRedactor:
    """Dependency that provides configured PiiRedactor instance"""
    return PiiRedactor(
        redaction_style="mask",
        recognizer_config_path="app/utils/pii_recognizers.yaml"
    )

@app.post("/chat")
async def chat_with_proxy(
    request: ChatRequest,
    redactor: PiiRedactor = Depends(get_redactor)
) -> dict:
    """
    Processes chat request through PII redaction and OpenAI API proxy
    
    - Request: ChatRequest object containing user message
    - Returns: OpenAI API response with generated content
    """
    try:
        # Redact sensitive information
        sanitized_query = redactor.redact_pii(request.message)
        logger.info(f"Processed query (length: {len(sanitized_query)})")

        system_message = "You will help testing a system that redacts personal information from inputs. Your task is to echo the exact content of the message provided by user."

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "AI-Chat-Proxy/1.0"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": sanitized_query}
            ],
            "temperature": 0.7
        }

        # Async HTTP request with timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENAI_API_URL,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenAI API error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail="Error processing request with AI service"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to AI service"
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request payload"
        )

@app.get("/health")
async def health_check() -> dict:
    """Service health check endpoint"""
    return {
        "status": "healthy",
        "version": app.version,
        "environment": os.getenv("ENVIRONMENT", "development")
    }