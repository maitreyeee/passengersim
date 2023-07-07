from __future__ import annotations

from pydantic import BaseModel, field_validator


class Path(BaseModel, extra="forbid"):
    orig: str
    dest: str
    path_quality_index: float

    legs: list[int]
    """Flight numbers of legs comprising the path."""

    @field_validator("legs", mode="before")
    def allow_single_leg(cls, v):
        """Allow a single leg path to be just an int not a list of one int."""
        if isinstance(v, int):
            v = [v]
        return v
