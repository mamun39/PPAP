from abc import ABC, abstractmethod

class BaseRedactor(ABC):
    """Base abstract class for redaction implementations"""
    
    @abstractmethod
    def redact_pii(self, text: str) -> str:
        """
        Redact PII from the given text.
        
        Args:
            text: Text to be redacted
            
        Returns:
            Text with PII redacted
        """
        pass