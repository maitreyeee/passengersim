# TITLE: Choice Models
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .named import Named


class PodsChoiceModel(Named, extra="forbid"):
    kind: Literal["pods"]

    emult: float | None = None
    basefare_mult: float | None = None
    connect_disutility: float | None = None
    path_quality: tuple[float, float] | None = None
    preferred_airline: tuple[float, float] | None = None
    r1: float | None = None
    r2: float | None = None
    r3: float | None = None
    r4: float | None = None
    tolerance: float | None = None
    non_stop_multiplier: float | None = None
    connection_multiplier: float | None = None


class LogitChoiceModel(Named, extra="forbid"):
    kind: Literal["logit"]

    intercept: float = 0
    """This is the alternative specific constant for the no-purchase alternative."""

    nonstop: float = 0
    duration: float = 0
    price: float = 0

    tod_sin2p: float = 0
    """Schedule parameter.

    If `t` is departure time (in minutes after midnight local time) divided
    by 1440, this parameter is multiplied by `sin( 2 \pi t)` and the result is
    added to the utility of the particular alternative."""

    tod_sin4p: float = 0
    """Schedule parameter.

    If `t` is departure time (in minutes after midnight local time) divided
    by 1440, this parameter is multiplied by `sin( 4 \pi t)` and the result is
    added to the utility of the particular alternative."""

    tod_sin6p: float = 0
    tod_cos2p: float = 0
    tod_cos4p: float = 0
    tod_cos6p: float = 0
    free_bag: float = 0
    early_boarding: float = 0
    same_day_change: float = 0


ChoiceModel = Annotated[PodsChoiceModel | LogitChoiceModel, Field(discriminator="kind")]
"""
Two types of choice models are available in AirSim.

Use the `kind` key to select which kind of choice model you wish to parameterize.
"""
