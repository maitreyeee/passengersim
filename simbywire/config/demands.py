from __future__ import annotations

from pydantic import BaseModel, field_validator


class Demand(BaseModel, extra="forbid"):
    orig: str
    dest: str
    segment: str
    base_demand: float
    reference_fare: float
    choice_model: str | None = None
    curve: str | None = None

    @property
    def choice_model_(self):
        """Choice model, falling back to segment name if not set explicitly."""
        return self.choice_model or self.segment

    @field_validator("curve", mode="before")
    def curve_integer_name(cls, v):
        """Booking curves can have integer names, treat as string."""
        if isinstance(v, int):
            v = str(v)
        return v
