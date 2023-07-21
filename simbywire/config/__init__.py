# TITLE: AirSimConfig
# DOC-NAME: 00-configs
from __future__ import annotations

import gzip
import importlib
import pathlib
import sys
import typing

import yaml
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
from .snapshot_filter import SnapshotFilter


class AirSimConfig(BaseModel, extra="forbid"):
    scenario: str = Field(default_factory=random_label)
    """Name for this scenario."""

    simulation_controls: SimulationSettings = SimulationSettings()
    db: DatabaseConfig = DatabaseConfig()
    rm_systems: DictOfNamed[RmSystem] = []
    choice_models: DictOfNamed[ChoiceModel] = {}
    airlines: DictOfNamed[Airline] = {}
    classes: list[str] = []
    dcps: list[int] = []
    """A list of DCPs (data collection points).

    The DCPs are given as integers, which represent the number of days
    before departure.
    """
    booking_curves: DictOfNamed[BookingCurve] = {}
    legs: list[Leg] = []
    demands: list[Demand] = []
    fares: list[Fare] = []
    paths: list[Path] = []

    snapshot_filters: list[SnapshotFilter] = []

    @model_validator(mode="after")
    def _airlines_have_rm_systems(cls, m: AirSimConfig):
        """Check that all airlines have RM systems that have been defined."""
        for airline in m.airlines.values():
            if airline.rm_system not in m.rm_systems:
                raise ValueError(
                    f"Airline {airline.name} has unknown RM system {airline.rm_system}"
                )
        return m

    @model_validator(mode="after")
    def _booking_curves_match_dcps(cls, m: AirSimConfig):
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

    @classmethod
    def _from_yaml(
        cls,
        filenames: pathlib.Path | list[pathlib.Path],
    ):
        """Read from YAML."""
        if isinstance(filenames, str | pathlib.Path):
            filenames = [filenames]
        raw_config = {}
        for filename in reversed(filenames):
            filename = pathlib.Path(filename)
            opener = gzip.open if filename.suffix == ".gz" else open
            with opener(filename) as f:
                content = yaml.safe_load(f)
                raw_config.update(content)
        return cls.model_validate(raw_config)

    @classmethod
    def from_yaml(
        cls,
        filenames: pathlib.Path | list[pathlib.Path],
    ):
        """Load AirSim config from YAML.

        This method reloads the config class to ensure all imported RmSteps
        are properly registered before loading the YAML instructions.
        """

        # reload these to refresh for any newly defined RmSteps
        importlib.reload(sys.modules.get(f"{__name__}.rm_systems"))
        module = importlib.reload(sys.modules.get(f"{__name__}"))

        reloaded_class = getattr(module, cls.__name__)
        if reloaded_class is None:
            raise RuntimeError(f"unable to reload {cls.__name__}")
        return reloaded_class._from_yaml(filenames)
