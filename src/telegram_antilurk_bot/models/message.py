"""Message archive model - TDD implementation."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class MessageArchive(Base):
    """Model for archiving messages from moderated channels."""

    __tablename__ = 'message_archive'

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Chat and message identifiers
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)

    # Message content
    text = Column(Text, nullable=True)
    message_type = Column(String(50), nullable=False, default='text')

    # Timestamps
    sent_at = Column(DateTime, nullable=False)
    edited_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Reply and forward information
    reply_to_message_id = Column(BigInteger, nullable=True)
    forward_from_chat_id = Column(BigInteger, nullable=True)
    forward_from_message_id = Column(BigInteger, nullable=True)
    forward_date = Column(DateTime, nullable=True)

    # Additional metadata as JSON
    extra_metadata = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", backref="messages")

    # Indexes for performance
    __table_args__ = (
        Index('ix_message_archive_chat_user', 'chat_id', 'user_id'),
        Index('ix_message_archive_chat_sent', 'chat_id', 'sent_at'),
        Index('ix_message_archive_user_sent', 'user_id', 'sent_at'),
        Index('ix_message_archive_chat_message', 'chat_id', 'message_id', unique=True),
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize message with archived_at timestamp."""
        super().__init__(**kwargs)
        if not self.archived_at:
            self.archived_at = datetime.utcnow()  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<MessageArchive(chat_id={self.chat_id}, message_id={self.message_id}, user_id={self.user_id})"

    @property
    def is_reply(self) -> bool:
        """Check if this message is a reply to another message."""
        return self.reply_to_message_id is not None

    @property
    def is_forward(self) -> bool:
        """Check if this message is forwarded from another chat."""
        return self.forward_from_chat_id is not None
