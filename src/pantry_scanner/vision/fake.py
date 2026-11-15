from pantry_scanner.vision.base import RawDetections


class FakeProvider:
    def __init__(self, response: RawDetections | Exception | None = None) -> None:
        self.response = response or RawDetections()
        self.calls: list[tuple[list[bytes], str, float]] = []

    def analyse(self, images: list[bytes], location: str, timeout_s: float) -> RawDetections:
        self.calls.append((images, location, timeout_s))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response
