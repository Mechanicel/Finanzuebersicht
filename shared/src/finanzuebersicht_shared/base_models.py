from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SharedModel(BaseModel):
    """Base model with strict defaults for all shared models."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, str_strip_whitespace=True)


class TimestampedModel(SharedModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
