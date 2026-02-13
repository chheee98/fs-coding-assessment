"""Custom HTTP exceptions for consistent error responses."""

from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Not authorized to access this resource"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
