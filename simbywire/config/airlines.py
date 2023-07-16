from __future__ import annotations

from .named import Named


class Airline(Named, extra="forbid"):
    """Configuration for AirSim.Airline object."""

    rm_system: str
    """Name of the revenue management system used by this airline."""
