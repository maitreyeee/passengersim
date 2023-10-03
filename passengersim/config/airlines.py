from __future__ import annotations

from typing import Literal, Optional

from .named import Named


class Airline(Named, extra="forbid"):
    """Configuration for passengersim.Airline object."""

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

    frat5: Optional[str] = ""
    """Named FRAT5 curve.  
    This is the default that will be applied if not found at a more detailed level
    """

