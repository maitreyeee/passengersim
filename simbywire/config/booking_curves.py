from __future__ import annotations

from .named import Named


class BookingCurve(Named, extra="forbid"):
    curve: dict[int, float]
