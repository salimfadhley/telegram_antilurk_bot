"""User model - TDD implementation."""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, JSON, Index
from .base import Base


class User(Base):
    """Model for tracking users across all moderated channels."""

    __tablename__ = 'users'

    # Primary key is the Telegram user_id
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Tracking timestamps
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_interaction_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Flags and roles stored as JSON
    flags = Column(JSON, default=dict)
    roles = Column(JSON, default=list)

    # Indexes for performance
    __table_args__ = (
        Index('ix_users_last_interaction', 'last_interaction_at'),
        Index('ix_users_username', 'username'),
    )

    def __init__(self, **kwargs):
        """Initialize user with timestamps."""
        super().__init__(**kwargs)
        now = datetime.utcnow()
        if not self.first_seen:
            self.first_seen = now
        if not self.last_seen:
            self.last_seen = now
        if not self.last_interaction_at:
            self.last_interaction_at = now

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"

    def update_last_seen(self):
        """Update the last_seen timestamp."""
        self.last_seen = datetime.utcnow()

    def update_interaction(self):
        """Update both last_seen and last_interaction_at timestamps."""
        now = datetime.utcnow()
        self.last_seen = now
        self.last_interaction_at = now

    def is_lurker(self, threshold_days: int) -> bool:
        """Check if user is a lurker based on threshold."""
        if not self.last_interaction_at:
            return True
        delta = datetime.utcnow() - self.last_interaction_at
        return delta.days >= threshold_days

    def is_protected(self) -> bool:
        """Check if user is protected from moderation actions."""
        if self.flags:
            if self.flags.get('is_admin') or self.flags.get('is_bot'):
                return True
        if self.roles:
            protected_roles = {'admin', 'moderator', 'vip', 'allowlisted'}
            return any(role in protected_roles for role in self.roles)
        return False