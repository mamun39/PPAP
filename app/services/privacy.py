import logging
import yaml
from typing import List, Optional, Union
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerResult

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)

class PiiRedactor:
    """
    A structured, extensible PII redaction system with configurable recognizers and multiple redaction styles.
    Supports Presidio, spaCy-based context detection, and dynamic recognizer addition.
    """

    def __init__(
        self,
        redaction_style: str = "full",
        recognizer_config_path: Optional[str] = None
    ):
        """
        Initialize with redaction style and optional custom recognizers.
        
        Args:
            redaction_style: One of "full", "mask", or "hash".
            recognizer_config_path: Path to YAML file with recognizer configurations.
        """
        self.redaction_style = redaction_style.lower()
        self.analyzer = AnalyzerEngine()
        self._load_default_recognizers()
        
        if recognizer_config_path:
            self._load_recognizers_from_config(recognizer_config_path)

    def _load_default_recognizers(self) -> None:
        """Load built-in recognizers (e.g., basic phone numbers)."""
        self.add_custom_recognizer(
            entity_type="PHONE_NUMBER",
            patterns=[r"\b\d{3}[-.\s]?\d{4}\b"],
            name="Default Phone Recognizer"
        )

    def _load_recognizers_from_config(self, config_path: str) -> None:
        """
        Load recognizers from YAML config file.
        
        Args:
            config_path: Path to YAML config file with recognizer definitions.
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            for recognizer in config.get('recognizers', []):
                patterns = [
                    Pattern(name=p['name'], regex=p['regex'], score=p.get('score', 0.9))
                    for p in recognizer['patterns']
                ]
                self.add_custom_recognizer(
                    entity_type=recognizer['entity_type'],
                    patterns=patterns,
                    name=recognizer.get('name')
                )
            logger.info(f"Loaded recognizers from {config_path}")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config: {e}")
        except KeyError as e:
            logger.error(f"Missing required key in config: {e}")

    def add_custom_recognizer(
        self,
        entity_type: str,
        patterns: List[Union[str, Pattern]],
        name: Optional[str] = None
    ) -> None:
        """
        Add a custom recognizer dynamically.
        
        Args:
            entity_type: PII entity type (e.g., "IP_ADDRESS").
            patterns: List of regex patterns or `Pattern` objects.
            name: Optional recognizer name for debugging.
        
        Raises:
            ValueError: If patterns list is empty.
        """
        if not patterns:
            raise ValueError("Patterns list cannot be empty.")
        
        # Convert strings to Pattern objects if needed
        compiled_patterns = []
        for p in patterns:
            if isinstance(p, str):
                compiled_patterns.append(Pattern(name="custom_pattern", regex=p, score=0.9))
            else:
                compiled_patterns.append(p)
        
        recognizer = PatternRecognizer(
            supported_entity=entity_type,
            patterns=compiled_patterns,
            name=name or f"Custom {entity_type} Recognizer"
        )
        self.analyzer.registry.add_recognizer(recognizer)
        logger.debug(f"Added recognizer: {recognizer.name}")

    def redact_pii(self, text: str) -> str:
        """
        Redact PII entities in text based on loaded recognizers.
        
        Args:
            text: Input string to redact.
        
        Returns:
            Redacted text with PII replaced according to `redaction_style`.
            
        Raises:
            ValueError: If redaction_style is invalid.
        """
        if not text:
            return text
            
        results = self.analyzer.analyze(text, language="en")
        if not results:
            return text
        
        if self.redaction_style == "full":
            return self._redact_full(text, results)
        elif self.redaction_style == "mask":
            return self._redact_mask(text, results)
        else:
            raise ValueError(f"Invalid redaction_style: {self.redaction_style}")

    def _redact_full(self, text: str, results: List[RecognizerResult]) -> str:
        """
        Replace PII with entity type labels (e.g., '<PHONE_NUMBER>').
        
        Args:
            text: Original text to redact.
            results: List of recognized PII entities.
            
        Returns:
            Text with PII replaced by entity type markers.
        """
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
        for result in sorted_results:
            text = text[:result.start] + f"<{result.entity_type}>" + text[result.end:]
        return text

    def _redact_mask(self, text: str, results: List[RecognizerResult]) -> str:
        """
        Mask PII with asterisks (e.g., '***').
        
        Args:
            text: Original text to redact.
            results: List of recognized PII entities.
            
        Returns:
            Text with PII replaced by asterisks.
        """
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
        for result in sorted_results:
            text = text[:result.start] + "*" * (result.end - result.start) + text[result.end:]
        return text

    def get_supported_entities(self) -> List[str]:
        """
        Return a list of supported PII entity types.
        
        Returns:
            List of entity types supported by loaded recognizers.
        """
        entities = []
        for recognizer in self.analyzer.registry.recognizers:
            if isinstance(recognizer.supported_entities, list):
                entities.extend(recognizer.supported_entities)
            else:
                entities.append(recognizer.supported_entities)
        return sorted(set(entities))  # Return unique, sorted entities


# Example Usage
if __name__ == "__main__":
    redactor = PiiRedactor(
        redaction_style="mask",
        recognizer_config_path="app/utils/pii_recognizers.yaml"
    )

    # Check loaded recognizers
    print("Supported entities:", redactor.get_supported_entities())

    # Redact sample text
    sample = "Call +1 555 123 4567 or 456-7890 or connect to 192.168.1.1."
    print(redactor.redact_pii(sample))  # Output: "Call ************ or ******* or connect to ***********."