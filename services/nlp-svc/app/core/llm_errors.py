"""LLM routing errors."""


class LLMUnavailableError(Exception):
    """Raised when no LLM tier (Anthropic, Ollama, etc.) is reachable."""

    def __init__(self, message: str = "LLM inference unavailable. Configure Tier 1 or Tier 2 endpoints in Admin."):
        super().__init__(message)
        self.message = message
