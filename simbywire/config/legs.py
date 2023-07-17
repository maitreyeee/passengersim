from __future__ import annotations

import time
from datetime import datetime, timedelta

from pydantic import BaseModel, FieldValidationInfo, field_validator


def create_timestamp(base_date, offset, hh, mm) -> int:
    """Create Unix time from base date, offset (days) and time"""
    td = timedelta(days=offset, hours=hh, minutes=mm)
    tmp = base_date + td
    return int(time.mktime(tmp.timetuple()))


class Leg(BaseModel, extra="forbid"):
    carrier: str
    fltno: int
    orig: str
    dest: str
    date: datetime = datetime.fromisoformat("2022-09-21")
    dep_time: int
    arr_time: int
    capacity: int
    distance: float | None = None

    @field_validator("date", mode="before")
    def _date_from_string(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        return v

    @field_validator("dep_time", "arr_time", mode="before")
    def _timestring_to_int(cls, v, info: FieldValidationInfo):
        if isinstance(v, str) and ":" in v:
            dep_time_str = v.split(":")
            hh, mm = int(dep_time_str[0]), int(dep_time_str[1])
            v = create_timestamp(info.data["date"], 0, hh, mm)
        if info.field_name == "arr_time":
            if v < info.data["dep_time"]:
                v += 86400  # add a day (in seconds) as arr time is next day
        return v
