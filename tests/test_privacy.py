import pytest
import os
import yaml
from pathlib import Path
from presidio_analyzer import Pattern

from app.services.privacy import PiiRedactor


@pytest.fixture
def sample_config_file(tmp_path):
    """Create a temporary sample config file for testing."""
    config = {
        "recognizers": [
            {
                "name": "Test Credit Card Recognizer",
                "entity_type": "CREDIT_CARD",
                "patterns": [
                    {"name": "credit_card_pattern", "regex": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "score": 0.8}
                ]
            },
            {
                "name": "Test Email Recognizer",
                "entity_type": "EMAIL_ADDRESS",
                "patterns": [
                    {"name": "email_pattern", "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "score": 0.9}
                ]
            }
        ]
    }
    
    config_path = tmp_path / "test_recognizers.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    return str(config_path)


class TestPiiRedactor:
    
    def test_initialization_defaults(self):
        """Test initialization with default parameters."""
        redactor = PiiRedactor()
        assert redactor.redaction_style == "full"
        assert redactor.analyzer is not None
    
    def test_initialization_with_custom_style(self):
        """Test initialization with custom redaction style."""
        redactor = PiiRedactor(redaction_style="mask")
        assert redactor.redaction_style == "mask"
    
    def test_initialization_with_invalid_style(self):
        """Test that invalid redaction style raises ValueError when redacting."""
        redactor = PiiRedactor(redaction_style="invalid")
        # Include text with a phone number which should be detected by the default recognizer
        with pytest.raises(ValueError, match="Invalid redaction_style"):
            redactor.redact_pii("My phone number is 123-4567")
    
    def test_load_recognizers_from_config(self, sample_config_file):
        """Test loading recognizers from config file."""
        redactor = PiiRedactor(recognizer_config_path=sample_config_file)
        supported_entities = redactor.get_supported_entities()
        
        # Flatten the list of supported entities
        flat_entities = [item for sublist in supported_entities for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        assert "CREDIT_CARD" in flat_entities
        assert "EMAIL_ADDRESS" in flat_entities
    
    def test_load_recognizers_from_nonexistent_config(self, caplog):
        """Test loading recognizers from a nonexistent config file."""
        redactor = PiiRedactor(recognizer_config_path="nonexistent_file.yaml")
        assert "Config file not found" in caplog.text
    
    def test_add_custom_recognizer_with_string_pattern(self):
        """Test adding a custom recognizer with a string pattern."""
        redactor = PiiRedactor()
        redactor.add_custom_recognizer(
            entity_type="IP_ADDRESS",
            patterns=[r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"],
            name="IP Address Recognizer"
        )
        
        # Test if the recognizer was added
        supported_entities = redactor.get_supported_entities()
        flat_entities = [item for sublist in supported_entities for item in (sublist if isinstance(sublist, list) else [sublist])]
        assert "IP_ADDRESS" in flat_entities
    
    def test_add_custom_recognizer_with_pattern_objects(self):
        """Test adding a custom recognizer with Pattern objects."""
        redactor = PiiRedactor()
        pattern = Pattern(name="ssn_pattern", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=0.95)
        
        redactor.add_custom_recognizer(
            entity_type="US_SSN",
            patterns=[pattern],
            name="SSN Recognizer"
        )
        
        supported_entities = redactor.get_supported_entities()
        flat_entities = [item for sublist in supported_entities for item in (sublist if isinstance(sublist, list) else [sublist])]
        assert "US_SSN" in flat_entities
    
    def test_add_custom_recognizer_with_empty_patterns(self):
        """Test adding a custom recognizer with empty patterns list."""
        redactor = PiiRedactor()
        with pytest.raises(ValueError, match="Patterns list cannot be empty"):
            redactor.add_custom_recognizer(entity_type="TEST", patterns=[])
    
    def test_redact_pii_full_style(self):
        """Test redacting PII with 'full' style."""
        redactor = PiiRedactor(redaction_style="full")
        text = "Call me at 123-4567 or email at test@example.com"
        
        # Add email recognizer for this test
        redactor.add_custom_recognizer(
            entity_type="EMAIL",
            patterns=[r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
            name="Email Recognizer"
        )
        
        redacted = redactor.redact_pii(text)
        assert "<PHONE_NUMBER>" in redacted
        assert "<EMAIL>" in redacted
        assert "123-4567" not in redacted
        assert "test@example.com" not in redacted
    
    def test_redact_pii_mask_style(self):
        """Test redacting PII with 'mask' style."""
        redactor = PiiRedactor(redaction_style="mask")
        text = "Call me at 123-4567"
        redacted = redactor.redact_pii(text)
        
        assert "Call me at " in redacted
        assert "123-4567" not in redacted
        assert "*******" in redacted  # 7 characters in "123-4567"
    
    def test_redact_pii_no_matches(self):
        """Test redacting text with no PII matches."""
        redactor = PiiRedactor()
        text = "This text has no PII"
        redacted = redactor.redact_pii(text)
        assert redacted == text
    
    def test_get_supported_entities(self):
        """Test retrieving supported entity types."""
        redactor = PiiRedactor()
        entities = redactor.get_supported_entities()
        assert isinstance(entities, list)
        # Default phone recognizer should be there
        flat_entities = [item for sublist in entities for item in (sublist if isinstance(sublist, list) else [sublist])]
        assert "PHONE_NUMBER" in flat_entities


if __name__ == "__main__":
    pytest.main(["-v", "test_privacy.py"])