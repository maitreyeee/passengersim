try:
    # before loading any other subpackages, first try to
    # load declarations of all the usual RmStep classes
    from passengersim_core import airline  # noqa: F401
except ImportError:
    pass

from ._version import __version__, __version_tuple__
from .config import Config
from .driver import Simulation
from .summary import SummaryTables

__all__ = [
    "Config",
    "Simulation",
    "SummaryTables",
    "demo_network",
    "__version__",
    "__version_tuple__",
]


def demo_network(name: str):
    import importlib.resources

    if not name.endswith(".yaml"):
        name = f"{name}.yaml"
    return importlib.resources.files(__package__).joinpath("networks").joinpath(name)


def versions():
    """Print the versions"""
    print(f"passengersim {__version__}")
    import passengersim_core
    print(f"passengersim.core {passengersim_core.__version__}")
