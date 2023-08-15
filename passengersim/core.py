try:
    import passengersim_core
except ImportError:
    raise
    import warnings
    warnings.warn("passengersim core is not available")
    passengersim_core = None
    SimulationEngine = None
else:
    from passengersim_core import SimulationEngine

__all__ = ['SimulationEngine']