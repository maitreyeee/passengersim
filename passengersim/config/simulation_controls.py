# TITLE: Simulation Controls
# DOC-NAME: 01-simulation-controls
from __future__ import annotations

from typing import Literal

from pydantic import FieldValidationInfo, confloat, conint, field_validator

from passengersim.utils import iso_to_unix

from .pretty import PrettyModel


class SimulationSettings(PrettyModel, extra="allow", validate_assignment=True):
    num_trials: conint(ge=1, le=1000) = 1
    """The overall number of trials to run.

    Each trial is a complete simulation, including burn-in training time as well
    as study time.  It will have a number of sequentially developed samples, each of
    which represents one "typical" day of travel.

    See [Counting Simulations][counting-simulations] for more details.
    """

    num_samples: conint(ge=1, le=1000) = 600
    """The number of samples to run within each trial.

    Each sample represents one "typical" day of travel.
    See [Counting Simulations][counting-simulations] for more details.
    """

    burn_samples: conint(ge=1, le=1000) = 100
    """The number of samples to burn when starting each trial.

    Burned samples are used to populate a stable history of data to support
    forecasting and optimization algorithms, but are not used to evaluate
    performance results.

    See [Counting Simulations][counting-simulations] for more details.
    """

    double_capacity_until: int | None = None
    """
    Double the capacity on all legs until this sample.

    The extra capacity may reduce the statistical noise of untruncation
    within the burn period and allow the simulation to achieve a stable
    steady state faster.  If used, this should be set to a value at least
    26 below the `burn_samples` value to avoid polluting the results.
    """

    @field_validator("double_capacity_until")
    @classmethod
    def _avoid_capacity_pollution(cls, v: int | None, info: FieldValidationInfo):
        if v and v >= info.data["burn_samples"] - 25:
            raise ValueError("doubled capacity will pollute results")
        return v

    sys_k_factor: confloat(gt=0, lt=5.0) = 0.10
    """
    System-level randomness factor.

    This factor controls the level of correlation in demand levels across the
    entire system.

    See [k-factors][demand-generation-k-factors]
    for more details.
    """

    mkt_k_factor: confloat(gt=0, lt=5.0) = 0.20
    """
    Market-level randomness factor.

    This factor controls the level of correlation in demand levels across origin-
    destination markets.

    See [k-factors][demand-generation-k-factors]
    for more details.
    """

    pax_type_k_factor: confloat(gt=0, lt=5.0) = 0.40
    """
    Passenger-type randomness factor.

    This factor controls the level of correlation in demand levels across passenger
    types.

    See [k-factors][demand-generation-k-factors]
    for more details.
    """

    tf_k_factor: confloat(gt=0) = 0.1
    """
    Time frame randomness factor.

    This factor controls the dispersion of bookings over time, given a previously
    identified level of total demand. See [k-factors]() for more details.
    """

    z_factor: confloat(gt=0, lt=100.0) = 2.0
    """
    Base level demand variance control.

    See [k-factors][demand-generation-k-factors] for more details.
    """

    prorate_revenue: bool = True

    dwm_lite: bool = True
    """
    Use the "lite" decision window model.

    The structure of this model is the same as that use by Boeing.
    """

    max_connect_time: conint(ge=0) = 240
    """
    Maximum connection time for automatically generated paths.

    Any generated path that has a connection time greater than this value (expressed
    in minutes) is invalidated.
    """

    disable_ap: bool = False
    """
    Remove all advance purchase settings used in the simulation.

    This applies to all airlines and all fare products.
    """

    demand_multiplier: confloat(gt=0) = 1.0
    """
    Scale all demand by this value.

    Setting to a value other than 1.0 will increase or decrease all demand inputs
    uniformly by the same multiplicative amount. This is helpful when exploring how
    simulation results vary when you have "low demand" scenarios (e.g,
    demand_multiplier = 0.8), or "high demand" scenarios (e.g., demand multiplier = 1.1).
    """

    manual_paths: bool = True
    """
    The user has provided explicit paths and connections.

    If set to False, the automatic path generation algorithm is applied.
    """

    write_raw_files: bool = False

    random_seed: int | None = None
    """
    Integer used to control the reproducibility of simulation results.

    A seed is base value used by a pseudo-random generator to generate random
    numbers. A fixed random seed is used to ensure the same randomness pattern
    is reproducible and does not change between simulation runs, i.e. allows
    subsequent runs to be conducted with the same randomness pattern as a
    previous one. Any value set here will allow results to be repeated.

    The random number generator is re-seeded at the beginning of every sample
    in every trial with a fixed tuple of three values: this "global" random seed,
    plus the sample number and trial number.  This ensures that partial results
    are also reproducible: the simulation of sample 234 in trial 2 will be the
    same regardless of how many samples are in trial 1.
    """

    update_frequency: int | None = None

    controller_time_zone: int | float = -21600
    """
    The reference time zone for the controller (seconds relative to UTC).

    Data collection points will be trigger at approximately midnight in this time zone.

    This value can be input in hours instead of seconds, any absolute value less
    than or equal to 12 will be assumed to be hours and scaled to seconds.

    The default value is -6 hours, or US Central Standard Time.
    """

    base_date: str = "2020-03-01"
    """
    The default date used to compute relative times for travel.

    Future enhancements may include multi-day modeling.
    """

    dcp_hour: float = 0.0
    """
    The hour of the day that the RM recalculation events are triggered.

    If set to zero, the events happen at midnight.  Other values can
    delay the recalculation into later in the night (or the next day).
    """

    show_progress_bar: bool = True
    """
    Show a progress bar while running.

    The progress display requires `rich` is installed.
    """

    @field_validator("controller_time_zone", mode="before")
    def _time_zone_convert_hours_to_seconds(cls, v):
        if -12 <= v <= 12:
            v *= 3600
        return v

    def reference_epoch(self) -> int:
        """Get the reference travel datetime in unix time."""
        return iso_to_unix(self.base_date) - self.controller_time_zone

    timeframe_demand_allocation: Literal["v2", "pods"] = "v2"
    """
    Which algorithm to use for time frame demand allocation.
    """
