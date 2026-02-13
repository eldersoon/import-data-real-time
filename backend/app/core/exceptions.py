"""Custom exceptions for the application"""


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class NotFoundError(Exception):
    """Raised when a resource is not found"""
    pass


class ProcessingError(Exception):
    """Raised when processing fails"""
    pass


class VehicleImportError(Exception):
    """Raised when vehicle import fails"""
    pass
