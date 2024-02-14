class BadAPICall(Exception):
    """Indicates that a BAD API Call was made"""

    def __init__(self, message="Bad API Call"):
        self.message = message
        super().__init__(self.message)


class BadAPIParams(Exception):
    """Indicates that a BAD API Call was made"""

    def __init__(self, message="Bad API Parameters"):
        self.message = message
        super().__init__(self.message)
