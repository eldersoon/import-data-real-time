"""Common API schemas"""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Standard message response"""
    message: str
