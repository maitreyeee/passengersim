# TITLE: Config
# DOC-NAME: 00-configs
from __future__ import annotations

import gzip
import importlib
import pathlib
import sys
import typing

import yaml
from pydantic import BaseModel, Field, model_validator

from passengersim.pseudonym import random_label

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


class Config(BaseModel, extra="forbid"):
    scenario: str = Field(default_factory=random_label)
    """Name for this scenario.

    The scenario name is helpful when writing different simulations to the same
    database so you can uniquely identify and query results for a particular
    scenario."""

    simulation_controls: SimulationSettings = SimulationSettings()
    """
    Controls that apply broadly to the overall simulation.
    
    See [passengersim.config.SimulationSettings][] for detailed documentation.
    """

    db: DatabaseConfig = DatabaseConfig()
    """
    See [passengersim.config.DatabaseConfig][] for detailed documentation.
    """

    rm_systems: DictOfNamed[RmSystem] = []
    """
    The revenue management systems used by the carriers in this simulation.
    
    See [RM Systems][rm-systems] for details.
    """

    choice_models: DictOfNamed[ChoiceModel] = {}
    """Several choice models are programmed behind the scenes.  The choice_models option allows the user to set the parameters used in the utility model for a particular choice model.

    There are two choice models currently programmed.

    Need to explaining more here"""

    airlines: DictOfNamed[Airline] = {}
    """A list of airlines.

    One convention is to use Airline1, Airline2, ... to list the airlines in the
    network.  Another convention is to use IATA industry-standard two-letter airline
    codes.  See the
    [IATA code search](https://www.iata.org/en/publications/directories/code-search/)
    for more information."""

    classes: list[str] = []
    """A list of fare classes.  
    
    One convention is to use Y0, Y1, ... to label fare classes from the highest 
    fare (Y0) to the lowest fare (Yn).  An example of classes is below.

    Example
    -------
    ```{yaml}
    classes:
      - Y0
      - Y1
      - Y2
      - Y3
      - Y4
      - Y5
    ```
    """

    dcps: list[int] = []
    """A list of DCPs (data collection points).

    The DCPs are given as integers, which represent the number of days
    before departure.   An example of data collection points is given below.  Note that as you get closer to day of departure (DCP=0) the number of days between two consecutive DCP periods
    decreases.  The DCP intervals are shorter because as you get closer to departure, customer arrival rates tend to increase, and it is advantageous to forecast changes in demand for shorter intervals.
    dcps:
  - 63
  - 56
  - 49
  - 42
  - 35
  - 31
  - 28
  - 24
  - 21
  - 17
  - 14
  - 10
  - 7
  - 5
  - 3
  - 1

    """

    booking_curves: DictOfNamed[BookingCurve] = {}
    """Booking curves
    An example of a booking curve is below.
    booking_curves:
  - name: c1
    curve:
      63: 0.06
      56: 0.11
      49: 0.15
      42: 0.2
      35: 0.23
      31: 0.25
      28: 0.28
      24: 0.31
      21: 0.35
      17: 0.4
      14: 0.5
      10: 0.62
      7: 0.7
      5: 0.78
      3: 0.95
      1: 1.0
"""
    legs: list[Leg] = []
    demands: list[Demand] = []
    fares: list[Fare] = []
    paths: list[Path] = []

    snapshot_filters: list[SnapshotFilter] = []

    @model_validator(mode="after")
    def _airlines_have_rm_systems(cls, m: Config):
        """Check that all airlines have RM systems that have been defined."""
        for airline in m.airlines.values():
            if airline.rm_system not in m.rm_systems:
                raise ValueError(
                    f"Airline {airline.name} has unknown RM system {airline.rm_system}"
                )
        return m

    @model_validator(mode="after")
    def _booking_curves_match_dcps(cls, m: Config):
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
    def from_yaml(
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
    def model_validate(
        cls,
        *args,
        **kwargs,
    ) -> typing.Self:
        """Validate the passengersim Config inputs.

        This method reloads the Config class to ensure all imported
        RmSteps are properly registered before validation.

        Args:
            obj: The object to validate.
            strict: Whether to raise an exception on invalid fields.
            from_attributes: Whether to extract data from object attributes.
            context: Additional context to pass to the validator.

        Raises:
            ValidationError: If the object could not be validated.

        Returns:
            The validated model instance.
        """
        # reload these to refresh for any newly defined RmSteps
        module_parent = ".".join(__name__.split(".")[:-1])
        importlib.reload(sys.modules.get(f"{module_parent}.rm_systems"))
        importlib.reload(sys.modules.get(__name__))
        module = importlib.reload(sys.modules.get(module_parent))
        reloaded_class = getattr(module, cls.__name__)
        # `__tracebackhide__` tells pytest and some other tools to omit this function from tracebacks
        __tracebackhide__ = True
        return reloaded_class.__pydantic_validator__.validate_python(*args, **kwargs)
