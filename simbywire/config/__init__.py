from pydantic import BaseModel, confloat, conint, model_validator

from .airlines import Airline
from .booking_curves import BookingCurve
from .choice_model import ChoiceModel
from .named import DictOfNamed
from .rm_systems import RmSystem


class AirSimConfig(BaseModel, extra="forbid"):
    scenario: str

    rm_systems: DictOfNamed[RmSystem] = []
    choice_models: DictOfNamed[ChoiceModel] = {}

    num_trials: conint(ge=1, le=1000) = 1
    """The overall number of trials to run.

    Each trial is a complete simulation, including burn-in training time as well
    as study time.
    """

    num_samples: conint(ge=1, le=1000) = 600
    """The number of samples to run within each trial.
    """

    sys_k_factor: confloat(gt=0, lt=5.0) = 0.10
    mkt_k_factor: confloat(gt=0, lt=5.0) = 0.20
    pax_type_k_factor: confloat(gt=0, lt=5.0) = 0.40
    tf_k_factor: confloat(gt=0, lt=5.0) = 0.1
    z_factor: confloat(gt=0, lt=5.0) = 2.0

    theft_nesting: bool = False
    prorate_revenue: bool = True

    dwm_lite: bool = True

    max_connect_time: conint(ge=0) = 240

    disable_ap: bool = False
    demand_multiplier: confloat(gt=0) = 1.0
    manual_paths: bool = True

    airlines: DictOfNamed[Airline]

    @model_validator(mode="after")
    def airlines_have_rm_systems(cls, m: "AirSimConfig"):
        """Check that all airlines have RM systems that have been defined."""
        for airline in m.airlines.values():
            if airline.rm_system not in m.rm_systems:
                raise ValueError(
                    f"Airline {airline.name} has unknown RM system {airline.rm_system}"
                )
        return m

    classes: list[str]
    dcps: list[int]

    booking_curves: DictOfNamed[BookingCurve]

    @model_validator(mode="after")
    def booking_curves_match_dcps(cls, m: "AirSimConfig"):
        """Check that all booking curves are complete and valid."""
        sorted_dcps = reversed(sorted(m.dcps))
        for curve in m.booking_curves.values():
            i = 0
            for dcp in sorted_dcps:
                assert (
                    dcp in curve.curve
                ), f"booking curve {curve.name} is missing dcp {dcp}"
                assert (
                    curve.curve[dcp] >= i
                ), f"booking curve {curve.name} moves backwards at dcp {dcp}"
                i = curve.curve[dcp]
        return m
