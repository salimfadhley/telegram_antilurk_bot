"""Callback handler for inline keyboard responses."""

import re

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from .modlog_notifier import ModlogNotifier
from .tracker import ProvocationTracker

logger = structlog.get_logger(__name__)


class CallbackHandler:
    """Handles inline keyboard button callbacks for challenges."""

    def __init__(self, tracker: ProvocationTracker | None = None, notifier: ModlogNotifier | None = None) -> None:
        """Initialize callback handler."""
        self.tracker = tracker or ProvocationTracker()
        self.notifier = notifier or ModlogNotifier()

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Handle callback query from inline keyboard button."""
        if not update.callback_query or not update.callback_query.data:
            return False

        callback_data = update.callback_query.data
        user_id = update.callback_query.from_user.id

        # Parse callback data: provocation_{id}_choice_{index}
        match = re.match(r'provocation_(\d+)_choice_(\d+)', callback_data)
        if not match:
            logger.warning("Invalid callback data format", callback_data=callback_data)
            return False

        provocation_id = int(match.group(1))
        choice_index = int(match.group(2))

        # Validate callback
        if not await self.tracker.validate_callback(provocation_id, user_id, choice_index):
            await update.callback_query.answer("❌ Invalid response.")
            return False

        # Check if answer is correct
        is_correct = await self.tracker.is_correct_choice(provocation_id, choice_index)

        if is_correct:
            # Correct answer
            await self.tracker.update_provocation_status(
                provocation_id, "completed", response_user_id=user_id
            )
            await update.callback_query.answer("✅ Correct! Welcome to the community.")

            # Edit message to show completion
            message = update.callback_query.message
            if message and hasattr(message, 'edit_text'):
                await message.edit_text(
                    f"✅ Challenge completed successfully by {update.callback_query.from_user.first_name or 'User'}!",
                    reply_markup=None
                )

            logger.info(
                "Challenge completed successfully",
                provocation_id=provocation_id,
                user_id=user_id
            )

        else:
            # Incorrect answer
            await self.tracker.update_provocation_status(
                provocation_id, "failed", response_user_id=user_id
            )
            await update.callback_query.answer("❌ Incorrect answer.")

            # Edit message to show failure
            message = update.callback_query.message
            if message and hasattr(message, 'edit_text'):
                await message.edit_text(
                    "❌ Challenge failed. Administrators have been notified.",
                    reply_markup=None
                )

            # Schedule modlog notification for kick
            await self.notifier.schedule_kick_notification(provocation_id)

            logger.info(
                "Challenge failed",
                provocation_id=provocation_id,
                user_id=user_id
            )

        return True
