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
        """Initialize callback handler.

        If dependencies are not provided, they are instantiated lazily during
        handling so tests can patch the classes at call time.
        """
        self.tracker = tracker
        self.notifier = notifier

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

        # Resolve dependencies lazily to allow runtime patching in tests
        tracker = self.tracker or ProvocationTracker()
        notifier = self.notifier or ModlogNotifier()

        # Validate callback
        if not await tracker.validate_callback(provocation_id, user_id, choice_index):
            await update.callback_query.answer("❌ Invalid response.")
            return False

        # Check if answer is correct
        is_correct = await tracker.is_correct_choice(provocation_id, choice_index)

        if is_correct:
            # Correct answer
            await tracker.update_provocation_status(
                provocation_id, "completed", response_user_id=user_id
            )
            await update.callback_query.answer("✅ Correct! Welcome to the community.")

            # Edit message to show completion
            message = update.callback_query.message
            if message is not None:
                edit = getattr(message, 'edit_text', None)
                if callable(edit):
                    result = edit(
                        f"✅ Challenge completed successfully by {getattr(update.callback_query.from_user, 'first_name', None) or 'User'}!",
                        reply_markup=None
                    )
                    try:
                        # If the result is awaitable, await it; otherwise it's a sync call
                        import inspect
                        if inspect.isawaitable(result):
                            await result
                    except TypeError:
                        # In case a Mock object causes unexpected non-awaitable behavior
                        pass

            logger.info(
                "Challenge completed successfully",
                provocation_id=provocation_id,
                user_id=user_id
            )

        else:
            # Incorrect answer
            await tracker.update_provocation_status(
                provocation_id, "failed", response_user_id=user_id
            )
            await update.callback_query.answer("❌ Incorrect answer.")

            # Edit message to show failure
            message = update.callback_query.message
            if message is not None:
                edit = getattr(message, 'edit_text', None)
                if callable(edit):
                    result = edit(
                        "❌ Challenge failed. Administrators have been notified.",
                        reply_markup=None
                    )
                    try:
                        import inspect
                        if inspect.isawaitable(result):
                            await result
                    except TypeError:
                        pass

            # Schedule modlog notification for kick
            await notifier.schedule_kick_notification(provocation_id)

            logger.info(
                "Challenge failed",
                provocation_id=provocation_id,
                user_id=user_id
            )

        return True
