class ScanProcessingError(Exception):
    def __init__(self, error_code: str) -> None:
        super().__init__(error_code)
        self.error_code = error_code


class ProviderTimeoutError(ScanProcessingError):
    def __init__(self) -> None:
        super().__init__("timeout")


class InvalidProviderOutputError(ScanProcessingError):
    def __init__(self) -> None:
        super().__init__("invalid_output")


class ProviderUnavailableError(ScanProcessingError):
    def __init__(self) -> None:
        super().__init__("provider_unavailable")
