import os
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv
from app.services.pattern_redactor import PatternRedactor
from app.services.llm_redactor import LlmRedactor
from app.services.redactor_base import BaseRedactor

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

# Get redactor configuration
REDACTOR_TYPE = os.getenv("REDACTOR_TYPE", "pattern").lower()  # 'pattern' or 'llm'
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
REDACTION_STYLE = os.getenv("REDACTION_STYLE", "mask")

app = FastAPI(title="Privacy-Preserving AI Proxy (PPAP)", version="1.0.0")

class ChatRequest(BaseModel):
    message: str = Field(..., 
        example="What's the weather in New York?",
        min_length=1,
        max_length=2000,
        description="User message to be processed")

async def get_redactor() -> BaseRedactor:
    """Dependency that provides configured redactor instance"""
    if REDACTOR_TYPE == "llm":
        logger.info(f"Using LLM redactor with model {LLM_MODEL}")
        return LlmRedactor(
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            redaction_style=REDACTION_STYLE
        )
    else:
        logger.info(f"Using pattern-based redactor")
        return PatternRedactor(
            redaction_style=REDACTION_STYLE,
            recognizer_config_path="app/utils/pii_recognizers.yaml"
        )

@app.post("/chat")
async def chat_with_proxy(
    request: ChatRequest,
    redactor: BaseRedactor = Depends(get_redactor)
) -> dict:
    """
    Processes chat request through PII redaction and OpenAI API proxy
    
    - Request: ChatRequest object containing user message
    - Returns: OpenAI API response with generated content
    """
    try:
        # Redact sensitive information using the configured redactor
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
        "environment": os.getenv("ENVIRONMENT", "development"),
        "redactor_type": REDACTOR_TYPE
    }