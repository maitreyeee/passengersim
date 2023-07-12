from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, ClassVar, Literal

from AirSim.airline import rm_emsr, rm_forecast, rm_untruncation
from pydantic import BaseModel, Field

from .named import Named


class RmStepBase(BaseModel, extra="forbid"):
    name: str = ""

    def _factory(self):
        kwargs = self.model_dump()
        # step_class = kwargs.pop("step_class")
        kwargs.pop("step_type")
        return self.step_class(**kwargs)


class UntruncationStep(RmStepBase, extra="forbid"):
    step_type: Literal["untruncation"]
    step_class: ClassVar[Callable] = rm_untruncation.UntruncationStep
    kind: Literal["leg", "path"] = "leg"
    algorithm: str


class ForecastStep(RmStepBase, extra="forbid"):
    step_type: Literal["forecast"]
    step_class: ClassVar[Callable] = rm_forecast.ForecastStep
    algorithm: str
    kind: Literal["leg", "path"] = "leg"
    alpha: float = 0.15


class OptimizationStep(RmStepBase, extra="forbid"):
    step_type: Literal["optimization"]
    step_class: ClassVar[Callable] = rm_emsr.OptimizationStep
    algorithm: str
    kind: Literal["leg", "path"] = "leg"


RmStep = Annotated[
    UntruncationStep | ForecastStep | OptimizationStep, Field(discriminator="step_type")
]


class RmSystem(Named, extra="forbid"):
    steps: list[RmStep]
