import pathlib
from typing import Literal

from pydantic import BaseModel, field_validator


class DatabaseConfig(BaseModel, extra="forbid", validate_assignment=True):
    engine: Literal["sqlite", "mysql", None] = "sqlite"
    """Database engine to use.

    Currently only `sqlite` is fully implemented."""

    filename: pathlib.Path | None = "airsim-output.sqlite"
    """Name of file for SQLite output."""

    fast: bool = False
    """Whether to use pre-compiled SQL write instructions."""

    pragmas: list[str] = []
    """A list of PRAGMA commands to execute upon opening a database connection."""

    commit_count_delay: int | None = 250
    """Commit transactions to the database will only be honored this frequently.

    By setting this number greater than 1, the transaction frequency will be reduced,
    improving overall runtime performance by storing more data in RAM and writing to
    persistent storage less frequently.
    """

    write_detail: set[str] = {"leg", "bucket", "fare", "demand"}
    """Which detailed items should be written to the database at each DCP."""

    @field_validator("engine", mode="before")
    def _interpret_none(cls, v):
        """Allow engine to be "none"."""
        if isinstance(v, str) and v.lower() == "none":
            v = None
        return v
