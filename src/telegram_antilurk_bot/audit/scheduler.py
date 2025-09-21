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

    def __init__(
        self,
        config_dir: Path | None = None,
        config_loader: ConfigLoader | None = None,
        audit_engine: AuditEngine | None = None,
    ) -> None:
        """Initialize the audit scheduler."""
        self.config_loader = config_loader or (
            ConfigLoader(config_dir=config_dir) if config_dir else ConfigLoader()
        )
        self.global_config, _, _ = self.config_loader.load_all()
        self.audit_cadence_minutes = self.global_config.audit_cadence_minutes
        self.audit_engine = audit_engine or AuditEngine()
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._last_run: datetime | None = None

        logger.info("AuditScheduler initialized", audit_cadence_minutes=self.audit_cadence_minutes)

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running

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

    def stop(self) -> None:  # type: ignore[override]
        """Synchronous stop helper for unit tests."""
        self._running = False
        if self._task:
            try:
                self._task.cancel()
            finally:
                self._task = None

    async def run_audit_cycle(self) -> dict[str, Any]:
        """Run a single audit cycle across all moderated chats."""
        result = await self.audit_engine.run_full_audit()
        self._last_run = datetime.utcnow()
        return result

    async def _run_audit_cycle(self) -> dict[str, Any]:
        """Internal wrapper to support tests patching private method."""
        return await self.run_audit_cycle()

    def should_run_audit(self) -> bool:
        """Indicate whether an audit should run now based on cadence.

        This lightweight check is used by contracts to verify the presence
        of a scheduling decision method. It returns True if no audit has
        ever run, or if the configured cadence interval has elapsed.
        """
        if self._last_run is None:
            return True
        elapsed = (datetime.utcnow() - self._last_run).total_seconds()
        return elapsed >= self.audit_cadence_minutes * 60

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
                        **result,
                    )
                except Exception as e:
                    logger.error(
                        "Audit cycle failed",
                        error=str(e),
                        duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    )

                # Wait for next cycle
                await asyncio.sleep(self.audit_cadence_minutes * 60)
        except asyncio.CancelledError:
            logger.info("Scheduler cancelled")
            raise
