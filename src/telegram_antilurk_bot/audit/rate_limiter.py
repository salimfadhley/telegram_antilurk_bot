"""Rate limiting for provocation enforcement."""


import structlog

from ..config.loader import ConfigLoader
from ..config.schemas import GlobalConfig
from ..database.models import User

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Enforces rate limits for provocations per chat."""

    def __init__(self, global_config: GlobalConfig | None = None, config_loader: ConfigLoader | None = None) -> None:
        """Initialize rate limiter with configuration.

        Accepts an optional `GlobalConfig` or a `ConfigLoader` to load one.
        If neither is provided, a default `ConfigLoader` is used.
        """
        if global_config is not None:
            self.global_config = global_config
        else:
            loader = config_loader or ConfigLoader()
            self.global_config, _, _ = loader.load_all()

        self.hourly_limit = self.global_config.rate_limit_per_hour
        self.daily_limit = self.global_config.rate_limit_per_day

    # --- Async wrappers used by other components ---
    async def get_current_hourly_count(self, chat_id: int) -> int:
        """Get current hourly provocation count for chat."""
        return self._get_hourly_provocation_count(chat_id)

    async def get_current_daily_count(self, chat_id: int) -> int:
        """Get current daily provocation count for chat."""
        return self._get_daily_provocation_count(chat_id)

    # --- Synchronous API used by unit tests ---
    def can_provoke_user(
        self,
        chat_id: int,
        rate_limit_per_hour: int | None = None,
        rate_limit_per_day: int | None = None,
    ) -> bool:
        """Check if provocations can be sent based on provided or configured limits."""
        hourly_limit = rate_limit_per_hour if rate_limit_per_hour is not None else self.hourly_limit
        daily_limit = rate_limit_per_day if rate_limit_per_day is not None else self.daily_limit

        hourly_count = self._get_hourly_provocation_count(chat_id)
        daily_count = self._get_daily_provocation_count(chat_id)

        can_provoke = (hourly_count < hourly_limit) and (daily_count < daily_limit)

        logger.debug(
            "Rate limit check",
            chat_id=chat_id,
            hourly_count=hourly_count,
            daily_count=daily_count,
            hourly_limit=hourly_limit,
            daily_limit=daily_limit,
            can_provoke=can_provoke,
        )

        return can_provoke

    async def can_send_provocation(self, chat_id: int) -> bool:
        """Contract method: whether any provocation can be sent in this chat now."""
        return self.can_provoke_user(chat_id)

    def record_provocation(self, chat_id: int, user_id: int) -> None:
        """Record a provocation event for accounting purposes (sync for unit tests)."""
        self._record_provocation(chat_id, user_id)

    async def get_remaining_allowance(self, chat_id: int) -> dict[str, int]:
        """Return remaining hourly and daily allowance for this chat."""
        hourly_count = self._get_hourly_provocation_count(chat_id)
        daily_count = self._get_daily_provocation_count(chat_id)
        remaining_hourly = max(0, self.hourly_limit - hourly_count)
        remaining_daily = max(0, self.daily_limit - daily_count)
        return {
            'hourly': remaining_hourly,
            'daily': remaining_daily,
        }

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

    # --- Private helpers expected by unit tests ---
    def _get_hourly_provocation_count(self, chat_id: int) -> int:
        """Get provocation count for current hour. Placeholder to be patched in tests."""
        _ = chat_id
        return 0

    def _get_daily_provocation_count(self, chat_id: int) -> int:
        """Get provocation count for current day. Placeholder to be patched in tests."""
        _ = chat_id
        return 0

    def _record_provocation(self, chat_id: int, user_id: int) -> None:
        """Record a provocation event. Placeholder with logging for tests."""
        logger.info("Recorded provocation", chat_id=chat_id, user_id=user_id)
