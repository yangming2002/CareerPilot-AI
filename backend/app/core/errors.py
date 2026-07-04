class LLMError(Exception):
    """Base class for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Network timeout or connection failure."""
    pass


class LLMResponseError(LLMError):
    """LLM returned empty or malformed response."""
    pass


class LLMSchemaError(LLMError):
    """Structured output failed schema validation after retries."""
    pass


class GuardRejectionError(LLMError):
    """Guard check failed — suggestions contain fabrication or unsupported claims."""

    def __init__(self, message: str, failures: list[dict]):
        super().__init__(message)
        self.failures = failures


class InputInsufficientError(LLMError):
    """Input text too short or nonsensical for meaningful analysis."""
    pass
