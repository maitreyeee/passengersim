from __future__ import annotations

from typing import Literal

from .named import Named


class Airline(Named, extra="forbid"):
    """Configuration for AirSim.Airline object."""

    rm_system: str
    """Name of the revenue management system used by this airline."""

    control: Literal["leg", "theft", "bp", "vn", "none"] = "leg"
    """Control method.
    
    Allowed values include:
    - "leg" (default): Uses leg-based controls.
    - "theft": Theft.
    - "bp": Bid price.
    - "vn": Virtual nesting.
    - "none": No controls.
    """
