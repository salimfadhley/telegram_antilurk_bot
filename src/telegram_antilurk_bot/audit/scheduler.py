"""Audit scheduler for running periodic lurker audits."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from ..config.loader import ConfigLoader
from .audit_engine import AuditEngine

logger = structlog.get_logger(__name__)


class AuditScheduler:
    """Scheduler for running periodic audits of lurker activity."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the audit scheduler."""
        self.config_loader = ConfigLoader(config_dir=config_dir) if config_dir else ConfigLoader()
        self.global_config, _, _ = self.config_loader.load_all()
        self.audit_cadence_minutes = self.global_config.audit_cadence_minutes
        self.audit_engine = AuditEngine()
        self._running = False
        self._task: asyncio.Task[None] | None = None

        logger.info(
            "AuditScheduler initialized",
            audit_cadence_minutes=self.audit_cadence_minutes
        )

    async def start(self) -> None:
        """Start the audit scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("Audit scheduler started")

    async def stop(self) -> None:
        """Stop the audit scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Audit scheduler stopped")

    async def run_audit_cycle(self) -> dict[str, Any]:
        """Run a single audit cycle across all moderated chats."""
        return await self.audit_engine.run_full_audit()

    async def _run_scheduler(self) -> None:
        """Main scheduler loop."""
        try:
            while self._running:
                start_time = datetime.utcnow()

                try:
                    result = await self.run_audit_cycle()
                    logger.info(
                        "Audit cycle completed",
                        duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                        **result
                    )
                except Exception as e:
                    logger.error(
                        "Audit cycle failed",
                        error=str(e),
                        duration_seconds=(datetime.utcnow() - start_time).total_seconds()
                    )

                # Wait for next cycle
                await asyncio.sleep(self.audit_cadence_minutes * 60)
        except asyncio.CancelledError:
            logger.info("Scheduler cancelled")
            raise
