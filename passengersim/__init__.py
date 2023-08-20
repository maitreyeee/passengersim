try:
    # before loading any other subpackages, first try to
    # load declarations of all the usual RmStep classes
    from passengersim_core import airline  # noqa: F401
except ImportError:
    pass

from ._version import __version__, __version_tuple__
from .config import Config
from .driver import Simulation

__all__ = ["Config", "Simulation", "demo_network", "__version__", "__version_tuple__"]


def demo_network(name):
    import importlib.resources

    return (
        importlib.resources.files(__package__)
        .joinpath("networks")
        .joinpath(f"{name}.yaml")
    )
