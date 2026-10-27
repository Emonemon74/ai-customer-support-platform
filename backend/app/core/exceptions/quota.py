class QuotaExceededError(Exception):
    """A per-user limit was reached (HTTP 429)."""

    def __init__(self, message: str = "Usage limit reached"):
        self.message = message
        super().__init__(self.message)


class CapacityError(Exception):
    """The whole service is over its daily budget (HTTP 503)."""

    def __init__(self, message: str = "The service is at capacity, try again later"):
        self.message = message
        super().__init__(self.message)
