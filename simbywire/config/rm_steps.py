# TITLE: RM Systems
from __future__ import annotations

import inspect
import operator
import typing
from collections.abc import Callable
from functools import reduce
from typing import Annotated, ClassVar, Literal

from AirSim.airline import rm_forecast, rm_untruncation
from pydantic import BaseModel, Field


class RmStepBase(BaseModel, extra="forbid"):
    __subclasses: ClassVar[set[type[RmStepBase]]] = set()

    def __init_subclass__(cls, **kwargs):
        """Capture a list of all concrete subclasses, including nested levels"""
        super().__init_subclass__(**kwargs)

        if inspect.isabstract(cls):
            return  # do not consider intermediate abstract base classes

        annotations = inspect.get_annotations(cls, eval_str=True)
        assert "step_type" in annotations, "step_type not in annotations"
        annotation_step_type = typing.get_origin(annotations["step_type"])
        assert annotation_step_type == Literal, (
            f"annotation {annotations['step_type']} for `{cls.__name__}.step_type` "
            f"is not Literal but {annotation_step_type}"
        )
        found_step_type = typing.get_args(annotations["step_type"])[0]
        if cls.__name__.lower().endswith("step"):
            assert found_step_type == cls.__name__.lower()[:-4], (
                f"annotation Literal value {found_step_type!r} "
                f"for `{cls.__name__}.step_type` is not the same as the class name "
                f"(omitting 'step' suffix)"
            )
        else:
            assert found_step_type == cls.__name__.lower(), (
                f"annotation Literal value {found_step_type!r} "
                f"for `{cls.__name__}.step_type` is not the same as the class name"
            )
        cls.__subclasses.add(cls)

    @classmethod
    def as_pydantic_field(cls):
        if len(cls.__subclasses) > 1:
            return Annotated[
                reduce(operator.__or__, cls.__subclasses),
                Field(discriminator="step_type"),
            ]
        else:
            return Annotated[reduce(operator.__or__, cls.__subclasses), Field()]

    name: str = ""

    def _factory(self):
        if hasattr(self, "step_class"):
            kwargs = self.model_dump()
            # step_class = kwargs.pop("step_class")
            kwargs.pop("step_type")
            return self.step_class(**kwargs)
        else:
            return self.model_copy(deep=True)


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
