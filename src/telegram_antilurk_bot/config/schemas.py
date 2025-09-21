"""Configuration schemas - implemented to pass tests."""

import hashlib
from datetime import datetime

import yaml
from pydantic import BaseModel, Field, field_validator


class ProvenanceInfo(BaseModel):
    """Tracks configuration changes."""

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = Field(default="bot-init")
    checksum: str | None = None


class GlobalConfig(BaseModel):
    """Global configuration with defaults."""

    lurk_threshold_days: int = Field(default=14, ge=1, le=365)
    provocation_interval_hours: int = Field(default=48, ge=1, le=168)
    audit_cadence_minutes: int = Field(default=15, ge=5, le=1440)
    rate_limit_per_hour: int = Field(default=2, ge=1, le=10)
    rate_limit_per_day: int = Field(default=15, ge=1, le=100)
    enable_nats: bool = Field(default=False)
    enable_announcements: bool = Field(default=False)
    provenance: ProvenanceInfo = Field(default_factory=ProvenanceInfo)

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum of config content."""
        config_dict = self.model_dump(exclude={"provenance"})
        content = yaml.dump(config_dict, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def update_provenance(self, updated_by: str = "bot-command") -> None:
        """Update provenance information."""
        self.provenance.updated_at = datetime.utcnow()
        self.provenance.updated_by = updated_by
        self.provenance.checksum = self.compute_checksum()


class PuzzleChoice(BaseModel):
    """A single choice in a puzzle."""

    text: str
    is_correct: bool = False


class Puzzle(BaseModel):
    """A challenge puzzle."""

    id: str
    type: str = Field(..., pattern="^(arithmetic|common_sense)$")
    question: str
    choices: list[str] = Field(..., min_length=3, max_length=4)

    @field_validator("choices")
    @classmethod
    def validate_choices(cls, v: list[str]) -> list[str]:
        """Validate that there are enough choices."""
        if len(v) < 3:
            raise ValueError(f"At least 3 choices required, found {len(v)}")
        return v

    def get_correct_answer(self) -> str:
        """Get the correct answer (always the first choice)."""
        return self.choices[0]

    def get_wrong_answers(self) -> list[str]:
        """Get the wrong answers (all choices except the first)."""
        return self.choices[1:]


class ChannelOverride(BaseModel):
    """Per-channel configuration overrides."""

    lurk_threshold_days: int | None = Field(None, ge=1, le=365)
    provocation_interval_hours: int | None = Field(None, ge=1, le=168)
    audit_cadence_minutes: int | None = Field(None, ge=5, le=1440)
    rate_limit_per_hour: int | None = Field(None, ge=1, le=10)
    rate_limit_per_day: int | None = Field(None, ge=1, le=100)


class ChannelEntry(BaseModel):
    """Channel configuration."""

    chat_id: int
    chat_name: str
    mode: str = Field(..., pattern="^(moderated|modlog)$")
    modlog_ref: int | None = None
    overrides: ChannelOverride | None = None
    link_code: str | None = None
    link_expires_at: datetime | None = None


class ChannelsConfig(BaseModel):
    """Channels configuration."""

    channels: list[ChannelEntry] = Field(default_factory=list)
    provenance: ProvenanceInfo = Field(default_factory=ProvenanceInfo)

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum."""
        config_dict = self.model_dump(exclude={"provenance"})
        content = yaml.dump(config_dict, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def update_provenance(self, updated_by: str = "bot-command") -> None:
        """Update provenance information."""
        self.provenance.updated_at = datetime.utcnow()
        self.provenance.updated_by = updated_by
        self.provenance.checksum = self.compute_checksum()

    def get_moderated_channels(self) -> list[ChannelEntry]:
        """Get all moderated channels."""
        return [ch for ch in self.channels if ch.mode == "moderated"]

    def get_modlog_channels(self) -> list[ChannelEntry]:
        """Get all modlog channels."""
        return [ch for ch in self.channels if ch.mode == "modlog"]

    def get_linked_modlog(self, chat_id: int) -> ChannelEntry | None:
        """Get the modlog channel linked to a moderated channel."""
        moderated = next((ch for ch in self.channels if ch.chat_id == chat_id), None)
        if moderated and moderated.modlog_ref:
            return next((ch for ch in self.channels if ch.chat_id == moderated.modlog_ref), None)
        return None


class PuzzlesConfig(BaseModel):
    """Puzzles configuration."""

    puzzles: list[Puzzle] = Field(default_factory=list)
    provenance: ProvenanceInfo = Field(default_factory=ProvenanceInfo)

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum."""
        config_dict = self.model_dump(exclude={"provenance"})
        content = yaml.dump(config_dict, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def update_provenance(self, updated_by: str = "bot-command") -> None:
        """Update provenance information."""
        self.provenance.updated_at = datetime.utcnow()
        self.provenance.updated_by = updated_by
        self.provenance.checksum = self.compute_checksum()
