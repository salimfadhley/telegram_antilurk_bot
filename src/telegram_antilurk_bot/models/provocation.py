"""Provocation model - TDD implementation."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import Base


class ProvocationOutcome(str, Enum):
    """Possible outcomes for a provocation challenge."""

    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class Provocation(Base):
    """Model for tracking provocation/challenge sessions."""

    __tablename__ = "provocations"

    # Primary key
    provocation_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Chat and user identifiers
    chat_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    # Challenge details
    puzzle_id = Column(String(50), nullable=False)
    puzzle_question = Column(String(500), nullable=False)
    correct_answer = Column(String(255), nullable=False)
    user_answer = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    # Outcome
    outcome: Column[ProvocationOutcome] = Column(
        SQLEnum(ProvocationOutcome), default=ProvocationOutcome.PENDING, nullable=False
    )

    # Telegram message ID for the challenge
    challenge_message_id = Column(BigInteger, nullable=True)

    # Callback data for inline buttons
    callback_data = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", backref="provocations")

    # Indexes for performance
    __table_args__ = (
        Index("ix_provocations_chat_user", "chat_id", "user_id"),
        Index("ix_provocations_user_created", "user_id", "created_at"),
        Index("ix_provocations_chat_created", "chat_id", "created_at"),
        Index("ix_provocations_outcome", "outcome"),
        Index("ix_provocations_expires", "expires_at"),
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provocation with defaults."""
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = datetime.utcnow()  # type: ignore[assignment]
        if not self.outcome:
            self.outcome = ProvocationOutcome.PENDING  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<Provocation(id={self.provocation_id}, user_id={self.user_id}, outcome={self.outcome})>"

    @property
    def is_expired(self) -> bool:
        """Check if the provocation has expired."""
        return bool(datetime.utcnow() > self.expires_at)

    @property
    def is_pending(self) -> bool:
        """Check if the provocation is still pending."""
        return bool(self.outcome == ProvocationOutcome.PENDING)

    def mark_sent(self, message_id: int) -> None:
        """Mark the provocation as sent with the message ID."""
        self.sent_at = datetime.utcnow()  # type: ignore[assignment]
        self.challenge_message_id = message_id  # type: ignore[assignment]

    def mark_responded(self, answer: str, is_correct: bool) -> None:
        """Mark the provocation as responded with the user's answer."""
        self.responded_at = datetime.utcnow()  # type: ignore[assignment]
        self.user_answer = answer  # type: ignore[assignment]
        self.outcome = ProvocationOutcome.CORRECT if is_correct else ProvocationOutcome.INCORRECT  # type: ignore[assignment]

    def mark_timeout(self) -> None:
        """Mark the provocation as timed out."""
        self.outcome = ProvocationOutcome.TIMEOUT  # type: ignore[assignment]

    def mark_cancelled(self) -> None:
        """Mark the provocation as cancelled."""
        self.outcome = ProvocationOutcome.CANCELLED  # type: ignore[assignment]
