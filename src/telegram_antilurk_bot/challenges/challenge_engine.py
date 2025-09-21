"""Main challenge engine coordinating the complete flow."""

import os
import random
from typing import Any

import structlog

from ..config.loader import ConfigLoader
from ..database.models import User
from .callback_handler import CallbackHandler
from .composer import ChallengeComposer
from .modlog_notifier import ModlogNotifier
from .tracker import ProvocationTracker

logger = structlog.get_logger(__name__)


class ChallengeEngine:
    """Main engine coordinating challenge flow."""

    def __init__(self) -> None:
        """Initialize challenge engine."""
        self.config_loader = ConfigLoader()
        self.composer = ChallengeComposer()
        self.tracker = ProvocationTracker()
        self.callback_handler = CallbackHandler()
        self.notifier = ModlogNotifier()

    async def start_challenge(self, chat_id: int, user: User) -> int:
        """Start a new challenge for the user."""
        # Load puzzle configuration
        global_config, channels_config, puzzles_config = self.config_loader.load_all()

        if not puzzles_config.puzzles:
            logger.error("No puzzles available")
            raise ValueError("No puzzles configured")

        # Select random puzzle
        puzzle = random.choice(puzzles_config.puzzles)

        # Create provocation record first to get ID
        bot_token = os.environ.get('TELEGRAM_TOKEN')
        if not bot_token:
            raise ValueError("TELEGRAM_TOKEN not configured")

        provocation_id = await self.tracker.create_provocation(
            chat_id=chat_id,
            user_id=user.user_id,
            puzzle_id=puzzle.id,
            message_id=0,  # Will be updated after posting
            expiration_minutes=30
        )

        # Post challenge message
        try:
            message_id = await self.composer.post_challenge(
                chat_id=chat_id,
                puzzle=puzzle,
                user=user,
                bot_token=bot_token,
                provocation_id=provocation_id
            )

            # Update provocation with message ID
            provocation = await self.tracker.get_provocation(provocation_id)
            if provocation:
                provocation.message_id = message_id

            logger.info(
                "Challenge started successfully",
                provocation_id=provocation_id,
                chat_id=chat_id,
                user_id=user.user_id,
                puzzle_id=puzzle.id,
                message_id=message_id
            )

            return provocation_id

        except Exception as e:
            logger.error(
                "Failed to post challenge",
                provocation_id=provocation_id,
                error=str(e)
            )
            # Mark provocation as failed
            await self.tracker.update_provocation_status(provocation_id, "failed")
            raise

    async def handle_user_response(
        self,
        provocation_id: int,
        user_id: int,
        correct: bool
    ) -> bool:
        """Handle user response to challenge (for testing purposes)."""
        if correct:
            await self.tracker.update_provocation_status(
                provocation_id, "completed", response_user_id=user_id
            )
            logger.info(
                "Challenge completed",
                provocation_id=provocation_id,
                user_id=user_id
            )
        else:
            await self.tracker.update_provocation_status(
                provocation_id, "failed", response_user_id=user_id
            )
            await self.notifier.schedule_kick_notification(provocation_id)
            logger.info(
                "Challenge failed, notification sent",
                provocation_id=provocation_id,
                user_id=user_id
            )

        return True

    async def process_expired_challenges(self) -> dict[str, Any]:
        """Process all expired challenges and send notifications."""
        expired_provocations = await self.tracker.get_expired_provocations()

        processed_count = 0
        notification_count = 0

        for provocation in expired_provocations:
            try:
                # Mark as expired
                await self.tracker.update_provocation_status(
                    provocation.provocation_id, "expired"
                )
                processed_count += 1

                # Send kick notification
                await self.notifier.schedule_kick_notification(
                    provocation.provocation_id
                )
                notification_count += 1

                logger.info(
                    "Expired challenge processed",
                    provocation_id=provocation.provocation_id,
                    user_id=provocation.user_id
                )

            except Exception as e:
                logger.error(
                    "Failed to process expired challenge",
                    provocation_id=provocation.provocation_id,
                    error=str(e)
                )

        result = {
            'expired_challenges': len(expired_provocations),
            'processed_count': processed_count,
            'notifications_sent': notification_count
        }

        logger.info("Expired challenges processed", **result)
        return result

    # --- Contract compatibility methods ---
    async def create_challenge(self, chat_id: int, user: User) -> int:
        """Contract alias for starting a challenge."""
        return await self.start_challenge(chat_id=chat_id, user=user)

    async def handle_challenge_response(
        self,
        provocation_id: int,
        user_id: int,
        correct: bool
    ) -> bool:
        """Contract alias for handling a user response."""
        return await self.handle_user_response(
            provocation_id=provocation_id,
            user_id=user_id,
            correct=correct,
        )

    async def can_create_challenge(self, chat_id: int, user: User) -> bool:
        """Indicate whether a new challenge can be created.

        Placeholder implementation always allows creation. Future versions may
        check for existing pending provocations or rate limits.
        """
        _ = (chat_id, user)
        return True

    async def cleanup_expired_challenges(self) -> dict[str, Any]:
        """Contract alias for processing expired challenges."""
        return await self.process_expired_challenges()
