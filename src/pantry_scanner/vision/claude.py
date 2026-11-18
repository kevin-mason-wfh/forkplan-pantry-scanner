from pantry_scanner.vision.base import RawDetections


class ClaudeProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def analyse(self, images: list[bytes], location: str, timeout_s: float) -> RawDetections:
        raise NotImplementedError("Claude provider adapter is deferred")
