# TITLE: Frat5 Curves
from __future__ import annotations

from pydantic import ValidationInfo, field_validator

from .named import Named


class Frat5Curve(Named, extra="forbid"):
    """
    FRAT5 = Fare Ratio at which 50% of customers will buy up to the higher fare.
    """

    curve: dict[int, float]
    """Define a Frat5 curve.


    The values (cumulative fraction of customers arriving) should increase
    monotonically as the keys (DCPs, e.g. days to departure) decrease.

    Example
    -------
    ```{yaml}
    - name: curve_C
      curve:
        63: 1.4
        56: 1.4
        49: 1.5
        42: 1.5
        35: 1.6
        31: 1.7
        28: 1.8
        24: 1.9
        21: 2.3
        17: 2.7
        14: 3.2
        10: 3.3
        7: 3.4
        5: 3.4
        3: 3.5
        1: 3.5
    ```
    """

    @field_validator("curve")
    def _frat5_curves_accumulate(cls, v: dict[int, float], info: ValidationInfo):
        """Check that all curve values do not decrease as DCP keys decrease."""
        sorted_dcps = reversed(sorted(v.keys()))
        i = 0
        for dcp in sorted_dcps:
            assert (
                v[dcp] >= i
            ), f"frat5 curve {info.data['name']} moves backwards at dcp {dcp}"
            i = v[dcp]
        return v
