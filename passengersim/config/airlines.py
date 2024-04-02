from __future__ import annotations

from typing import Any

from .named import Named


class Airline(Named, extra="forbid"):
    """Configuration for passengersim.Airline object."""

    rm_system: str
    """Name of the revenue management system used by this airline."""

    control: str = ""
    """Deprecated.  No effect"""

    continuous_pricing: bool | None = False
    """Used to select continuous pricing"""

    frat5: str | None = ""
    """Named FRAT5 curve.
    This is the default that will be applied if not found at a more detailed level
    """

    load_factor_curve: Any | None = None
    """Named FRAT5 curve.
    This is the default that will be applied if not found at a more detailed level
    """

    ancillaries: dict[str, float] | None = {}
    """Specifies ancillaries offered by the airline, codes are ANC1 .. ANC4"""
