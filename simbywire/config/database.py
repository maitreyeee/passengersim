import pathlib
from typing import Literal

from pydantic import BaseModel


class DatabaseConfig(BaseModel, extra="forbid"):
    engine: Literal["sqlite", "mysql"] = "sqlite"
    filename: pathlib.Path | None = "airsim-output.sqlite"
