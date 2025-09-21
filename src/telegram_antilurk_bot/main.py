"""Main entry point for the Telegram Anti-Lurk Bot."""

import asyncio
import os
import signal
import sys
from datetime import datetime

import structlog
from telegram.ext import Application

from .config.loader import ConfigLoader
from .core.bot import BotApplication

logger = structlog.get_logger(__name__)


class BotRunner:
    """Main bot runner with startup and shutdown lifecycle management."""

    def __init__(self) -> None:
        """Initialize bot runner."""
        self.config_loader = ConfigLoader()
        self.bot_app: BotApplication | None = None
        self.telegram_app: Application | None = None
        self._shutdown_requested = False

    async def startup(self) -> None:
        """Handle bot startup sequence with notifications."""
        logger.info("Starting Telegram Anti-Lurk Bot", version="1.0.0")

        try:
            # Load configuration
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            logger.info("Configuration loaded successfully")

            # Initialize bot application
            self.bot_app = BotApplication(
                config_loader=self.config_loader
            )

            # Get Telegram token
            telegram_token = os.environ.get('TELEGRAM_TOKEN')
            if not telegram_token:
                logger.error("TELEGRAM_TOKEN environment variable not set")
                raise ValueError("TELEGRAM_TOKEN environment variable is required")

            # Initialize Telegram application
            self.telegram_app = Application.builder().token(telegram_token).build()

            # Register handlers
            await self.bot_app.register_handlers(self.telegram_app)

            # Send startup notifications to modlog channels
            await self._send_startup_notifications()

            logger.info("Bot startup completed successfully")

        except Exception as e:
            logger.error("Failed to start bot", error=str(e))
            raise

    async def run(self) -> None:
        """Run the bot with graceful shutdown handling."""
        if not self.telegram_app:
            raise RuntimeError("Bot not initialized. Call startup() first.")

        # Set up signal handlers for graceful shutdown
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

        try:
            # Start the bot
            logger.info("Bot is now running...")
            await self.telegram_app.run_polling(  # type: ignore[func-returns-value]
                poll_interval=1.0,
                drop_pending_updates=True,
                close_loop=False
            )

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error("Bot runtime error", error=str(e))
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Handle bot shutdown sequence with notifications."""
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        logger.info("Initiating bot shutdown sequence")

        try:
            # Send shutdown notifications to modlog channels
            await self._send_shutdown_notifications()

            # Persist any in-memory state
            if self.bot_app:
                await self.bot_app.persist_state()

            # Stop Telegram application
            if self.telegram_app and self.telegram_app.running:
                await self.telegram_app.stop()

            logger.info("Bot shutdown completed successfully")

        except Exception as e:
            logger.error("Error during shutdown", error=str(e))

    def _signal_handler(self, signum: int, frame: object) -> None:
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
        # Schedule shutdown coroutine
        if not self._shutdown_requested:
            asyncio.create_task(self.shutdown())

    async def _send_startup_notifications(self) -> None:
        """Send startup notifications to all modlog channels."""
        try:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            modlog_channels = channels_config.get_modlog_channels()

            if not modlog_channels:
                logger.info("No modlog channels configured for startup notifications")
                return

            startup_message = (
                "🟢 **Bot Startup Notice**\n\n"
                f"Telegram Anti-Lurk Bot has started successfully.\n"
                f"• Version: 1.0.0\n"
                f"• Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"• Monitoring {len(channels_config.get_moderated_channels())} moderated chats\n"
                f"• Configuration loaded from: {self.config_loader.config_dir}\n\n"
                "Bot is now actively monitoring for lurker activity."
            )

            if self.telegram_app:
                for modlog in modlog_channels:
                    try:
                        await self.telegram_app.bot.send_message(
                            chat_id=modlog.chat_id,
                            text=startup_message,
                            parse_mode='Markdown'
                        )
                        logger.info(
                            "Startup notification sent",
                            modlog_chat_id=modlog.chat_id,
                            modlog_name=modlog.chat_name
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to send startup notification",
                            modlog_chat_id=modlog.chat_id,
                            error=str(e)
                        )

        except Exception as e:
            logger.error("Failed to send startup notifications", error=str(e))

    async def _send_shutdown_notifications(self) -> None:
        """Send shutdown notifications to all modlog channels."""
        try:
            global_config, channels_config, puzzles_config = self.config_loader.load_all()
            modlog_channels = channels_config.get_modlog_channels()

            if not modlog_channels or not self.telegram_app:
                return

            shutdown_message = (
                "🔴 **Bot Shutdown Notice**\n\n"
                f"Telegram Anti-Lurk Bot is shutting down.\n"
                f"• Shutdown at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"• All configuration has been saved\n"
                f"• Active challenges will be restored on restart\n\n"
                "Service will resume when the bot is restarted."
            )

            for modlog in modlog_channels:
                try:
                    await self.telegram_app.bot.send_message(
                        chat_id=modlog.chat_id,
                        text=shutdown_message,
                        parse_mode='Markdown'
                    )
                    logger.info(
                        "Shutdown notification sent",
                        modlog_chat_id=modlog.chat_id,
                        modlog_name=modlog.chat_name
                    )
                except Exception as e:
                    logger.error(
                        "Failed to send shutdown notification",
                        modlog_chat_id=modlog.chat_id,
                        error=str(e)
                    )

        except Exception as e:
            logger.error("Failed to send shutdown notifications", error=str(e))


async def main() -> None:
    """Main entry point for the bot application."""
    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            min_level=os.environ.get('LOG_LEVEL', 'INFO').upper()
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create and run bot
    runner = BotRunner()

    try:
        await runner.startup()
        await runner.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)
    finally:
        await runner.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error("Application failed to start", error=str(e))
        sys.exit(1)
