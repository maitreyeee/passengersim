# TITLE: RM Systems
from __future__ import annotations

from .named import Named
from .rm_steps import RmStepBase

RmStep = RmStepBase.as_pydantic_field()


class RmSystem(Named, extra="forbid"):
    steps: list[RmStep]
