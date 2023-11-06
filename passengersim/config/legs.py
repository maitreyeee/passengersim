from __future__ import annotations

import time
from datetime import datetime, timedelta

from pydantic import BaseModel, ValidationInfo, field_validator


def create_timestamp(base_date, offset, hh, mm) -> int:
    """Create Unix time from base date, offset (days) and time"""
    td = timedelta(days=offset, hours=hh, minutes=mm)
    tmp = base_date + td
    return int(time.mktime(tmp.timetuple()))


class Leg(BaseModel, extra="forbid"):
    carrier: str
    fltno: int
    """A unique identifier for this leg.

    Each leg in a network should have a globally unique identifier (i.e. even
    if the carrier is different, `fltno` values should be unique.
    """

    orig: str
    """Origination location for this leg."""

    dest: str
    """Destination location for this leg."""

    date: datetime = datetime.fromisoformat("2020-03-01")
    """Date for this leg."""

    dep_time: int
    """Departure time for this leg in Unix time.

    In input files, this can be specified as a string in the format "HH:MM",
    with the hour in 24-hour format.

    Unix time is the number of seconds since 00:00:00 UTC on 1 Jan 1970."""

    arr_time: int
    """Arrival time for this leg in Unix time.

    In input files, this can be specified as a string in the format "HH:MM",
    with the hour in 24-hour format.

    Unix time is the number of seconds since 00:00:00 UTC on 1 Jan 1970."""

    capacity: int
    distance: float | None = None

    @field_validator("date", mode="before")
    def _date_from_string(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        return v

    @field_validator("dep_time", "arr_time", mode="before")
    def _timestring_to_int(cls, v, info: ValidationInfo):
        if isinstance(v, str) and ":" in v:
            dep_time_str = v.split(":")
            hh, mm = int(dep_time_str[0]), int(dep_time_str[1])
            v = create_timestamp(info.data["date"], 0, hh, mm)
        if info.field_name == "arr_time":
            if v < info.data["dep_time"]:
                v += 86400  # add a day (in seconds) as arr time is next day
        return v
