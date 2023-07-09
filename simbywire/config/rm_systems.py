from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .named import Named


class UntruncationStep(BaseModel, extra="forbid"):
    name: str = ""
    step_type: Literal["untruncation"]
    kind: Literal["leg", "path"] = "leg"
    algorithm: str


class ForecastStep(BaseModel, extra="forbid"):
    name: str = ""
    step_type: Literal["forecast"]
    algorithm: str
    kind: Literal["leg", "path"] = "leg"
    alpha: float = 0.15


class OptimizationStep(BaseModel, extra="forbid"):
    name: str = ""
    step_type: Literal["optimization"]
    algorithm: str


RmStep = Annotated[
    UntruncationStep | ForecastStep | OptimizationStep, Field(discriminator="step_type")
]


class RmSystem(Named, extra="forbid"):
    steps: list[RmStep]
