try:
    # before loading any other subpackages, first try to
    # load declarations of all the usual RmStep classes
    from AirSim import airline  # noqa: F401
except ImportError:
    pass

from .config import AirSimConfig
from .driver import Simulation

__all__ = ["AirSimConfig", "Simulation", "demo_network"]


def demo_network(name):
    import importlib.resources

    return (
        importlib.resources.files(__package__)
        .joinpath("networks")
        .joinpath(f"{name}.yaml")
    )
