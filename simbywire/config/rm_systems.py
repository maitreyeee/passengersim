# TITLE: RM Systems
from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, ClassVar, Literal

from AirSim.airline import rm_emsr, rm_forecast, rm_untruncation
from pydantic import BaseModel, Field, model_validator

from .named import Named
from .rm_steps import RmStep


class RmSystem(Named, extra="forbid"):
    steps: list[RmStep]
