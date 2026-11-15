from pantry_scanner.vision.base import VisionProvider
from pantry_scanner.vision.claude import ClaudeProvider
from pantry_scanner.vision.openai import OpenAIProvider


def create_provider(provider: str, model: str, api_key: str) -> VisionProvider:
    if provider == "claude":
        return ClaudeProvider(api_key, model)
    if provider == "openai":
        return OpenAIProvider(api_key, model)
    raise ValueError(f"Unsupported vision provider: {provider}")
