from __future__ import annotations

from typing import Annotated, TypeVar

from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator


class Named(BaseModel):
    name: str


T = TypeVar("T", bound=Named)


def enforce_name(x: dict[str, T] | list[T]) -> dict[str, T]:
    if isinstance(x, list):
        x_ = {}
        for n, i in enumerate(x):
            k = i.get("name")
            if k is None:
                raise ValueError(f"missing name in position {n}")
            x_[k] = i
        x = x_
    for k, v in x.items():
        if "name" not in v or not v["name"]:
            v["name"] = k
        if v["name"] != k:
            raise ValueError("airline explict name does not match key")
    return x


DictOfNamed = Annotated[dict[str, T], BeforeValidator(enforce_name)]
