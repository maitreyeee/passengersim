import pathlib
from typing import Literal

from pydantic import BaseModel


class DatabaseConfig(BaseModel, extra="forbid"):
    engine: Literal["sqlite", "mysql", None] = "sqlite"
    filename: pathlib.Path | None = "airsim-output.sqlite"
