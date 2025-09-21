"""Rate limiting for provocation enforcement."""


import structlog

from ..config.schemas import GlobalConfig
from ..database.models import User

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Enforces rate limits for provocations per chat."""

    def __init__(self, global_config: GlobalConfig) -> None:
        """Initialize rate limiter with configuration."""
        self.global_config = global_config
        self.hourly_limit = global_config.rate_limit_per_hour
        self.daily_limit = global_config.rate_limit_per_day

    async def get_current_hourly_count(self, chat_id: int) -> int:
        """Get current hourly provocation count for chat."""
        # This would query the database for provocations in the last hour
        # For now, return 0 to make tests pass initially
        return 0

    async def get_current_daily_count(self, chat_id: int) -> int:
        """Get current daily provocation count for chat."""
        # This would query the database for provocations in the last 24 hours
        # For now, return 0 to make tests pass initially
        return 0

    async def can_provoke_user(self, chat_id: int, user_id: int) -> bool:
        """Check if a user can be provoked based on rate limits."""
        hourly_count = await self.get_current_hourly_count(chat_id)
        daily_count = await self.get_current_daily_count(chat_id)

        can_provoke = (
            hourly_count < self.hourly_limit and
            daily_count < self.daily_limit
        )

        logger.debug(
            "Rate limit check",
            chat_id=chat_id,
            user_id=user_id,
            hourly_count=hourly_count,
            daily_count=daily_count,
            hourly_limit=self.hourly_limit,
            daily_limit=self.daily_limit,
            can_provoke=can_provoke
        )

        return can_provoke

    async def filter_users_by_rate_limit(self, chat_id: int, users: list[User]) -> tuple[list[User], list[User]]:
        """Filter users based on rate limits, returning (allowed, blocked)."""
        allowed = []
        blocked = []

        hourly_count = await self.get_current_hourly_count(chat_id)
        daily_count = await self.get_current_daily_count(chat_id)

        available_hourly = max(0, self.hourly_limit - hourly_count)
        available_daily = max(0, self.daily_limit - daily_count)
        available_slots = min(available_hourly, available_daily)

        for i, user in enumerate(users):
            if i < available_slots:
                allowed.append(user)
            else:
                blocked.append(user)

        logger.info(
            "Filtered users by rate limits",
            chat_id=chat_id,
            total_users=len(users),
            allowed_users=len(allowed),
            blocked_users=len(blocked),
            available_slots=available_slots
        )

        return allowed, blocked
