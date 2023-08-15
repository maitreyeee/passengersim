import warnings

try:
    import passengersim_core
except ImportError:
    warnings.warn("passengersim.core is not available", stacklevel=2)
    Airline = None
    BookingCurve = None
    Bucket = None
    ChoiceModel = None
    Demand = None
    Event = None
    Fare = None
    Forecast = None
    Generator = None
    Leg = None
    Market = None
    Path = None
    PathClass = None
    ProBP = None
    SimulationEngine = None
else:
    from passengersim_core import (
        Airline,
        BookingCurve,
        Bucket,
        ChoiceModel,
        Demand,
        Event,
        Fare,
        Forecast,
        Generator,
        Leg,
        Market,
        Path,
        PathClass,
        ProBP,
        SimulationEngine,
    )

__all__ = [
    "Airline",
    "BookingCurve",
    "Bucket",
    "ChoiceModel",
    "Demand",
    "Event",
    "Fare",
    "Forecast",
    "Generator",
    "Leg",
    "Market",
    "Path",
    "PathClass",
    "ProBP",
    "SimulationEngine",
]
