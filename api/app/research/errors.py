class ResearchError(Exception):
    """A research-storage outcome translated at the HTTP boundary."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
