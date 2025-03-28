import re
import spacy

# Load spaCy model for entity recognition
nlp = spacy.load("en_core_web_sm")

def scrub_pii(text):
    # Regular expressions for PII types
    patterns = {
        "name": r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)+",  # Matches first and last name
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Matches email
        # "phone": r"\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b"  # Matches phone number TODO: phone number doesn't work, resolve later
    }

    # Redact name, email, and phone using regex
    for label, pattern in patterns.items():
        text = re.sub(pattern, "[REDACTED]", text)

    # Use spaCy to detect other named entities like locations, etc.
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'PERSON', 'ORG', 'LOC']:  # Redact GPE, PERSON, etc.
            text = text.replace(ent.text, "[REDACTED]")

    return text