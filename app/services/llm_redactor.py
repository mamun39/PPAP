import argparse
import json
import logging
import re
import requests
from typing import Dict, List, Tuple, Set, Any, Optional

from app.services.redactor_base import BaseRedactor

logger = logging.getLogger(__name__)

class LlmRedactor(BaseRedactor):
    """
    A hybrid PII redaction system that uses an LLM to identify PII,
    then performs redaction programmatically for better performance and control.
    """

    def __init__(
        self,
        model_name: str = "llama3",
        ollama_base_url: str = "http://localhost:11434",
        redaction_style: str = "mask",
        temperature: float = 0.1
    ):
        """
        Initialize the hybrid LLM detector and programmatic redactor.
        
        Args:
            model_name: Name of the Ollama model to use
            ollama_base_url: Base URL for Ollama API
            redaction_style: One of "full", "mask", or "tag"
            temperature: Model temperature (lower for more deterministic results)
        """
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.redaction_style = redaction_style.lower()
        self.temperature = temperature
        self.api_url = f"{self.ollama_base_url}/api/generate"
        
        # Validate model availability
        self._validate_model()

    def _validate_model(self) -> None:
        """Validate that the specified model is available in Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                available_models = [model["name"] for model in response.json().get("models", [])]
                if self.model_name not in available_models:
                    logger.warning(f"Model '{self.model_name}' not found in Ollama. Available models: {', '.join(available_models)}")
            else:
                logger.warning(f"Could not verify model availability: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Error connecting to Ollama: {str(e)}")
            logger.warning("Continuing anyway, but make sure Ollama is running")

    def _create_detection_prompt(self, text: str) -> str:
        """
        Create a prompt instructing the LLM to identify PII.
        
        Args:
            text: The text to analyze
            
        Returns:
            A formatted prompt for the LLM
        """
        return f"""
You are a privacy analysis system designed to identify personally identifiable information (PII) in text.

List all instances of the following types of PII in the text:
- Names of people
- Phone numbers
- Email addresses
- Physical addresses 
- Social security numbers
- Credit card numbers
- IP addresses
- Dates of birth
- Account numbers
- Passport numbers
- License numbers
- Any other unique identifiers

Your task is to output a JSON object listing all PII found in the text.

IMPORTANT DETAILS:
- Country and city names are NOT considered PII unless they're part of a complete address
- General information and common knowledge are NOT PII
- Only include actual personal identifiers, not general words

INSTRUCTIONS FOR POSITION INDEXES:
- To find the start index, count characters from the beginning of the text.
- The first character is at position 0.
- The end index should be the position AFTER the last character of the PII.
- Spaces and punctuation count as characters.

Example of correct position indexes:
For the text: "Hello, my name is John Smith"
"John Smith" starts at index 18 and ends at index 28

IMPORTANT: Enclose your final JSON output between <PII> and </PII> delimiters.

Example format:

<PII>
{{
  "PERSON_NAME": [
    {{"text": "John Smith", "start": 18, "end": 28}}
  ],
  "PHONE_NUMBER": [
    {{"text": "(555) 123-4567", "start": 42, "end": 56}}
  ]
}}
</PII>

TEXT TO ANALYZE:
{text}
"""

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from a response text that should be enclosed in <PII></PII> tags.
        
        Args:
            response_text: Text response from LLM
            
        Returns:
            Parsed JSON object, or empty dict if parsing fails
        """
        # First try to extract content between the PII tags
        pii_pattern = r"<PII>([\s\S]*?)</PII>"
        match = re.search(pii_pattern, response_text)
        print(response_text)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing error in delimited content: {e}")
        else:
            # Some LLMs might mix up the order of tags, try to find anything between tags
            open_tag = response_text.find("<PII>")
            close_tag = response_text.find("</PII>")
            
            if open_tag >= 0 and close_tag >= 0:
                # Handle case where tags might be in wrong order
                start_pos = min(open_tag, close_tag) + 5  # Length of <PII>
                end_pos = max(open_tag, close_tag)
                
                if end_pos > start_pos:
                    json_str = response_text[start_pos:end_pos].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.warning("Could not parse JSON between malformed tags")
                
        # Fallback: try to find a JSON object anywhere in the response
        try:
            # Find the first { and the matching last }
            json_start = response_text.find("{")
            if json_start >= 0:
                # Track nested braces to find the correct closing brace
                brace_count = 0
                for i, char in enumerate(response_text[json_start:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response_text[json_start:json_start+i+1]
                            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Fallback JSON parsing error: {e}")
        
        logger.warning("Could not extract valid JSON from LLM response")
        return {}

    def _find_positions_in_text(self, text: str, pii_items: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find the correct positions of PII items in the text when LLM positions are unreliable.
        
        Args:
            text: Original text to analyze
            pii_items: Dictionary of PII items with potentially incorrect positions
            
        Returns:
            Updated dictionary with corrected positions
        """
        corrected_pii = {}
        
        for pii_type, items in pii_items.items():
            corrected_items = []
            for item in items:
                pii_text = item.get("text", "")
                if not pii_text:
                    continue
                    
                # Escape special regex characters
                escaped_text = re.escape(pii_text)
                
                # Find all occurrences in the text
                matches = list(re.finditer(escaped_text, text))
                
                if matches:
                    # Add all occurrences
                    for match in matches:
                        corrected_items.append({
                            "text": pii_text,
                            "start": match.start(),
                            "end": match.end()
                        })
                else:
                    # If no exact match found, try case-insensitive search
                    matches = list(re.finditer(escaped_text, text, re.IGNORECASE))
                    if matches:
                        for match in matches:
                            matched_text = match.group(0)  # Use the actual text found
                            corrected_items.append({
                                "text": matched_text,
                                "start": match.start(),
                                "end": match.end()
                            })
                    else:
                        # If still no match, keep the original item but mark it as unverified
                        logger.warning(f"Could not find '{pii_text}' in the original text")
                        # Only include if start and end are specified
                        if "start" in item and "end" in item:
                            corrected_items.append(item)
            
            if corrected_items:
                corrected_pii[pii_type] = corrected_items
                
        return corrected_pii

    def _detect_pii(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Use the LLM to detect PII instances in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping PII types to lists of detected instances with positions
        """
        if not text:
            return {}
            
        prompt = self._create_detection_prompt(text)
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": False
            }
            
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            output = result.get("response", "").strip()
            
            # Extract JSON data from LLM response
            pii_data = self._extract_json_from_response(output)
            
            if not pii_data:
                logger.warning("No PII data detected or could not parse LLM response")
                return {}
                
            # Correct positions by searching in the original text
            return self._find_positions_in_text(text, pii_data)
                
        except requests.RequestException as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in PII detection: {str(e)}")
            return {}

    def redact_pii(self, text: str) -> str:
        """
        Redact PII from text by first detecting with LLM, then redacting programmatically.
        
        Args:
            text: Text to redact
            
        Returns:
            Text with PII redacted according to selected style
        """
        if not text or len(text.strip()) == 0:
            return text
            
        # Detect PII using LLM
        pii_data = self._detect_pii(text)
        
        if not pii_data:
            logger.info("No PII detected in text")
            return text
        
        # Sort all PII instances by position (end index) in reverse order to avoid index shifting
        all_pii_instances = []
        for pii_type, instances in pii_data.items():
            for instance in instances:
                # Validate the instance data contains required fields
                if all(k in instance for k in ["text", "start", "end"]):
                    all_pii_instances.append({
                        "text": instance["text"], 
                        "start": instance["start"], 
                        "end": instance["end"],
                        "type": pii_type
                    })
        
        # Sort by end index in descending order
        all_pii_instances.sort(key=lambda x: x["end"], reverse=True)
        
        # Apply redaction according to style
        redacted_text = text
        for instance in all_pii_instances:
            pii_text = instance["text"]
            pii_type = instance["type"]
            start = instance["start"]
            end = instance["end"]
            
            # Skip if out of range (handles possible LLM errors)
            if start < 0 or end > len(redacted_text) or start >= end:
                logger.warning(f"Invalid PII position: {pii_type} at {start}:{end}")
                continue
                
            # Apply redaction according to the style
            if self.redaction_style == "mask":
                replacement = "*" * len(pii_text)
            elif self.redaction_style == "full":
                replacement = f"<{pii_type}>"
            elif self.redaction_style == "tag":
                replacement = f"[{pii_type}:{pii_text}]"
            else:
                replacement = "***"  # Default fallback
                
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
            
        return redacted_text

# Command-line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redact PII using Ollama LLM models")
    parser.add_argument("--model", default="llama3.2:3b", help="Ollama model name")
    parser.add_argument("--style", default="mask", choices=["mask", "full", "tag"], 
                        help="Redaction style")
    parser.add_argument("--url", default="http://localhost:11434", 
                        help="Ollama API URL")
    parser.add_argument("--text", required=True, help="Text to redact")
    
    args = parser.parse_args()
    
    redactor = LlmRedactor(
        model_name=args.model,
        ollama_base_url=args.url,
        redaction_style=args.style
    )
    
    print("\nOriginal Text:")
    print(args.text)
    
    print("\nRedacted Text:")
    redacted_text = redactor.redact_pii(args.text)
    print(redacted_text)
    