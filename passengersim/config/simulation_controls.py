# TITLE: Simulation Controls
# DOC-NAME: 01-simulation-controls
from __future__ import annotations

from pydantic import BaseModel, confloat, conint


class SimulationSettings(BaseModel, extra="allow"):
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

    tf_k_factor: confloat(gt=0, lt=5.0) = 0.1
    """
    Time frame randomness factor.

    This factor controls the dispersion of bookings over time, given a previously 
    identified level of total demand. See [k-factors]() for more details.
    """

    z_factor: confloat(gt=0, lt=5.0) = 2.0
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

    update_frequency: int | None = None