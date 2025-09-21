"""Compatibility shim for ChallengeEngine import path.

Tests import `telegram_antilurk_bot.challenges.engine.ChallengeEngine`.
This module re-exports the implementation from `challenge_engine`.
"""

from .challenge_engine import ChallengeEngine  # noqa: F401

