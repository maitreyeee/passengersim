from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from simbywire.pseudonym import random_label

from .airlines import Airline
from .booking_curves import BookingCurve
from .choice_model import ChoiceModel
from .database import DatabaseConfig
from .demands import Demand
from .fares import Fare
from .legs import Leg
from .named import DictOfNamed
from .paths import Path
from .rm_systems import RmSystem
from .simulation_controls import SimulationSettings


class AirSimConfig(BaseModel, extra="forbid"):
    scenario: str = Field(default_factory=random_label)

    simulation_controls: SimulationSettings = SimulationSettings()
    db: DatabaseConfig = DatabaseConfig()
    rm_systems: DictOfNamed[RmSystem] = []
    choice_models: DictOfNamed[ChoiceModel] = {}
    airlines: DictOfNamed[Airline] = {}
    classes: list[str] = []
    dcps: list[int] = []
    booking_curves: DictOfNamed[BookingCurve] = {}
    legs: list[Leg] = []
    demands: list[Demand] = []
    fares: list[Fare] = []
    paths: list[Path] = []

    @model_validator(mode="after")
    def airlines_have_rm_systems(cls, m: AirSimConfig):
        """Check that all airlines have RM systems that have been defined."""
        for airline in m.airlines.values():
            if airline.rm_system not in m.rm_systems:
                raise ValueError(
                    f"Airline {airline.name} has unknown RM system {airline.rm_system}"
                )
        return m

    @model_validator(mode="after")
    def booking_curves_match_dcps(cls, m: AirSimConfig):
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
