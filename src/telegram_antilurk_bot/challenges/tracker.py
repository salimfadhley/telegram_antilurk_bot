"""Provocation tracking and database persistence."""

from datetime import datetime, timedelta

import structlog

from ..database.models import Provocation

logger = structlog.get_logger(__name__)


class ProvocationTracker:
    """Tracks challenge provocations in the database."""

    def __init__(self) -> None:
        """Initialize provocation tracker."""
        # In-memory storage for Phase 5 - will be replaced with database in Phase 2
        self._provocations: dict[int, Provocation] = {}
        self._next_id = 1

    async def create_provocation(
        self,
        chat_id: int,
        user_id: int,
        puzzle_id: str,
        message_id: int,
        expiration_minutes: int = 30
    ) -> int:
        """Create new provocation record."""
        provocation_id = self._next_id
        self._next_id += 1

        expiration_date = datetime.utcnow() + timedelta(minutes=expiration_minutes)

        provocation = Provocation(
            provocation_id=provocation_id,
            chat_id=chat_id,
            user_id=user_id,
            puzzle_id=puzzle_id,
            provocation_date=datetime.utcnow(),
            expiration_date=expiration_date,
            status="pending"
        )

        self._provocations[provocation_id] = provocation

        logger.info(
            "Provocation created",
            provocation_id=provocation_id,
            chat_id=chat_id,
            user_id=user_id,
            puzzle_id=puzzle_id,
            expires_at=expiration_date
        )

        return provocation_id

    async def get_provocation(self, provocation_id: int) -> Provocation | None:
        """Get provocation by ID."""
        return self._provocations.get(provocation_id)

    async def is_provocation_expired(self, provocation_id: int) -> bool:
        """Check if provocation has expired."""
        provocation = self._provocations.get(provocation_id)
        if not provocation:
            return True

        return datetime.utcnow() > provocation.expiration_date

    async def update_provocation_status(
        self,
        provocation_id: int,
        status: str,
        response_user_id: int | None = None
    ) -> bool:
        """Update provocation status."""
        provocation = self._provocations.get(provocation_id)
        if not provocation:
            return False

        provocation.status = status
        if response_user_id is not None:
            provocation.response_date = datetime.utcnow()

        logger.info(
            "Provocation status updated",
            provocation_id=provocation_id,
            status=status,
            response_user_id=response_user_id
        )

        return True

    async def validate_callback(
        self,
        provocation_id: int,
        user_id: int,
        choice_index: int
    ) -> bool:
        """Validate that callback is from the correct user."""
        provocation = self._provocations.get(provocation_id)
        if not provocation:
            return False

        # Only the challenged user can respond
        if provocation.user_id != user_id:
            logger.warning(
                "Unauthorized callback attempt",
                provocation_id=provocation_id,
                expected_user=provocation.user_id,
                actual_user=user_id
            )
            return False

        # Check if already responded
        if provocation.status != "pending":
            logger.warning(
                "Callback for non-pending provocation",
                provocation_id=provocation_id,
                status=provocation.status
            )
            return False

        # Check if expired
        if await self.is_provocation_expired(provocation_id):
            logger.warning(
                "Callback for expired provocation",
                provocation_id=provocation_id
            )
            return False

        return True

    async def is_correct_choice(self, provocation_id: int, choice_index: int) -> bool:
        """Check if the chosen answer is correct."""
        # This would check against the puzzle choices
        # For now, assume choice index 1 is correct (placeholder)
        return choice_index == 1

    async def get_expired_provocations(self) -> list[Provocation]:
        """Get all expired provocations that haven't been processed."""
        current_time = datetime.utcnow()
        expired = []

        for provocation in self._provocations.values():
            if (provocation.status == "pending" and
                current_time > provocation.expiration_date):
                expired.append(provocation)

        return expired
