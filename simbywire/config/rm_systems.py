from typing import Annotated, Literal

from pydantic import BaseModel, Field


class UntruncationStep(BaseModel, extra="forbid"):
    name: str = ""
    step_type: Literal["untruncation"]
    kind: Literal["leg", "path"] = "leg"
    algorithm: str


class ForecastStep(BaseModel, extra="forbid"):
    name: str = ""
    step_type: Literal["forecast"]
    algorithm: str
    alpha: float = 0.15


class OptimizationStep(BaseModel, extra="forbid"):
    name: str = ""
    step_type: Literal["optimization"]
    algorithm: str


RmStep = Annotated[
    UntruncationStep | ForecastStep | OptimizationStep, Field(discriminator="step_type")
]


class RmSystem(BaseModel, extra="forbid"):
    name: str
    steps: list[RmStep]
