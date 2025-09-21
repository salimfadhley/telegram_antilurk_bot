"""Challenge message composition and posting."""

import random

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

from ..config.schemas import Puzzle
from ..database.models import User

logger = structlog.get_logger(__name__)


class ChallengeComposer:
    """Composes and posts challenge messages to Telegram."""

    def compose_challenge_message(self, puzzle: Puzzle, user: User) -> tuple[str, InlineKeyboardMarkup]:
        """Compose challenge message text and inline keyboard."""
        # Create user mention
        if user.username:
            user_mention = f"@{user.username}"
        elif user.first_name:
            user_mention = user.first_name
        else:
            user_mention = f"User {user.user_id}"

        # Compose message text
        message_text = (
            f"🧩 **Challenge for {user_mention}**\n\n"
            f"{puzzle.question}\n\n"
            f"⏰ You have 30 minutes to respond."
        )

        # Create randomized inline keyboard
        choices = puzzle.choices.copy()
        random.shuffle(choices)

        keyboard_buttons = []
        for i, choice in enumerate(choices):
            button = InlineKeyboardButton(
                text=choice,
                callback_data=f"provocation_{{provocation_id}}_choice_{i}"
            )
            keyboard_buttons.append([button])

        reply_markup = InlineKeyboardMarkup(keyboard_buttons)

        return message_text, reply_markup

    async def post_challenge(
        self,
        chat_id: int,
        puzzle: Puzzle,
        user: User,
        bot_token: str,
        provocation_id: int | None = None
    ) -> int:
        """Post challenge message to chat and return message ID."""
        message_text, reply_markup = self.compose_challenge_message(puzzle, user)

        # Replace placeholder with actual provocation ID if provided
        if provocation_id is not None:
            # Update callback data with actual provocation ID
            new_buttons = []
            for row in reply_markup.inline_keyboard:
                new_row = []
                for button in row:
                    callback_data_str = str(button.callback_data or "")
                    new_callback_data = callback_data_str.replace(
                        "{provocation_id}", str(provocation_id)
                    )
                    new_button = InlineKeyboardButton(
                        text=button.text,
                        callback_data=new_callback_data
                    )
                    new_row.append(new_button)
                new_buttons.append(new_row)
            reply_markup = InlineKeyboardMarkup(new_buttons)

        # Send message using Telegram Bot API
        app = Application.builder().token(bot_token).build()

        message = await app.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        logger.info(
            "Challenge posted",
            chat_id=chat_id,
            user_id=user.user_id,
            puzzle_id=puzzle.id,
            message_id=message.message_id,
            provocation_id=provocation_id
        )

        return message.message_id
