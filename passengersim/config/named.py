"""This module contains utilities for managing named objects."""

from __future__ import annotations

from typing import Annotated, TypeVar

from pydantic.functional_validators import BeforeValidator

from .pretty import PrettyModel


class Named(PrettyModel):
    name: str


T = TypeVar("T", bound=Named)


def enforce_name(x: dict[str, T] | list[T]) -> dict[str, T]:
    """Enforce that each item has a unique name.

    If you provide a list, this will ensure that each item in the list has a name.
    If you provide a dict, the names are given by the keys of the dictionary, and
    this will ensure that for each value, if it also has an explicitly defined name,
    that name matches its key-derived name.
    """
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
            raise ValueError("explict name does not match key")
    return x


DictOfNamed = Annotated[dict[str, T], BeforeValidator(enforce_name)]
