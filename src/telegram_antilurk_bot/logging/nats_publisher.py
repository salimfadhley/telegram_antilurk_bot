"""Optional NATS event publishing for external integrations."""

import json
import os
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class NATSEventPublisher:
    """Publishes events to NATS when configured."""

    def __init__(self) -> None:
        """Initialize NATS publisher."""
        self.nats_url = os.environ.get('NATS_URL')
        self.subject_prefix = os.environ.get('NATS_SUBJECT_PREFIX', 'antilurk')
        self.enabled = bool(self.nats_url)

        if self.enabled:
            logger.info("NATS publishing enabled", nats_url=self.nats_url)
        else:
            logger.debug("NATS publishing disabled - no NATS_URL configured")

    async def publish_event(self, subject: str, event_data: dict[str, Any]) -> bool:
        """Publish event to NATS if enabled."""
        if not self.enabled:
            logger.debug("Skipping NATS publish - not enabled")
            return False

        try:
            # Import nats here to avoid dependency if not used
            import nats

            # Connect to NATS
            assert self.nats_url is not None  # mypy: we already checked self.enabled
            nc = await nats.connect(self.nats_url)

            # Prepare subject with prefix
            full_subject = f"{self.subject_prefix}.{subject}"

            # Serialize event data
            message_data = json.dumps(event_data, default=str).encode()

            # Publish message
            await nc.publish(full_subject, message_data)
            await nc.close()

            logger.info(
                "Event published to NATS",
                subject=full_subject,
                event_type=event_data.get('event_type', 'unknown')
            )

            return True

        except ImportError:
            logger.warning("NATS library not available - install 'nats-py' to enable NATS publishing")
            return False
        except Exception as e:
            logger.error(
                "Failed to publish event to NATS",
                subject=subject,
                error=str(e),
                nats_url=self.nats_url
            )
            return False

    async def publish_challenge_failed(
        self,
        chat_id: int,
        user_id: int,
        provocation_id: int
    ) -> None:
        """Publish challenge failed event."""
        if not self.enabled:
            return

        event_data = {
            'event_type': 'challenge_failed',
            'chat_id': chat_id,
            'user_id': user_id,
            'provocation_id': provocation_id,
            'timestamp': self._get_timestamp()
        }

        await self.publish_event('challenge.failed', event_data)

    async def publish_challenge_completed(
        self,
        chat_id: int,
        user_id: int,
        provocation_id: int
    ) -> None:
        """Publish challenge completed event."""
        if not self.enabled:
            return

        event_data = {
            'event_type': 'challenge_completed',
            'chat_id': chat_id,
            'user_id': user_id,
            'provocation_id': provocation_id,
            'timestamp': self._get_timestamp()
        }

        await self.publish_event('challenge.completed', event_data)

    async def publish_user_kicked(
        self,
        chat_id: int,
        user_id: int,
        admin_user_id: int,
        reason: str = "failed_challenge"
    ) -> None:
        """Publish user kicked event."""
        if not self.enabled:
            return

        event_data = {
            'event_type': 'user_kicked',
            'chat_id': chat_id,
            'user_id': user_id,
            'admin_user_id': admin_user_id,
            'reason': reason,
            'timestamp': self._get_timestamp()
        }

        await self.publish_event('user.kicked', event_data)

    async def publish_audit_completed(
        self,
        processed_chats: int,
        total_lurkers: int,
        total_provoked: int
    ) -> None:
        """Publish audit cycle completed event."""
        if not self.enabled:
            return

        event_data = {
            'event_type': 'audit_completed',
            'processed_chats': processed_chats,
            'total_lurkers': total_lurkers,
            'total_provoked': total_provoked,
            'timestamp': self._get_timestamp()
        }

        await self.publish_event('audit.completed', event_data)

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
