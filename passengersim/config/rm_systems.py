# TITLE: RM Systems
from __future__ import annotations

from typing import Literal

from .named import Named
from .rm_steps import RmStepBase

RmStep = RmStepBase.as_pydantic_field()


class RmSystem(Named, extra="forbid"):
    steps: list[RmStep]

    availability_control: Literal["infer", "leg", "theft", "bp", "vn", "none"] = "infer"
    """Fare class availability algorithm for carriers using this RmSystem.

    The default value will infer the appropriate control based on the step_type
    of the last step in `steps`. (This is pending implementation).

    Allowed values include:
    - "leg" (default): Uses leg-based controls.
    - "bp": Bid price controls.
    - "vn": Virtual nesting.
    - "none": No controls.
    """
