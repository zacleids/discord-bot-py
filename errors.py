

class InvalidInputError(Exception):
    """Custom exception for invalid input."""
    def __init__(self, message="Invalid input provided"):
        super().__init__(message)

