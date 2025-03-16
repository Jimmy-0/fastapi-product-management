class NotFoundException(Exception):
    """Exception raised when a requested resource is not found."""
    def __init__(self, detail: str = "Resource not found"):
        self.detail = detail
        super().__init__(self.detail)

class ValidationException(Exception):
    """Exception raised for validation errors."""
    def __init__(self, detail: str = "Validation error"):
        self.detail = detail
        super().__init__(self.detail)

class DatabaseException(Exception):
    """Exception raised for database errors."""
    def __init__(self, detail: str = "Database error"):
        self.detail = detail
        super().__init__(self.detail)