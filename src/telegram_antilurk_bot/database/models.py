"""Database models for the anti-lurk bot."""

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """User model representing a Telegram user."""

    user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    last_message_at: datetime | None = None
    join_date: datetime | None = None
    is_bot: bool = False
    is_admin: bool = False

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class MessageArchive(BaseModel):
    """Message archive model for storing chat messages."""

    message_id: int
    chat_id: int
    user_id: int
    message_text: str | None = None
    message_date: datetime
    message_type: str = "text"

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class Provocation(BaseModel):
    """Provocation model for tracking challenge sessions."""

    provocation_id: int
    chat_id: int
    user_id: int
    puzzle_id: str
    provocation_date: datetime
    expiration_date: datetime
    status: str  # "pending", "completed", "failed", "expired"
    response_date: datetime | None = None
    message_id: int = 0

    class Config:
        """Pydantic configuration."""
        from_attributes = True
