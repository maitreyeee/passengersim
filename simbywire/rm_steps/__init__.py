#
# A step in the RM system
#  - Untruncation / Forecasting / Adjustments / Optimization / etc.
#  - This is the abstract base class, each component will inherit from this
#  - It defines the means to link the processing steps and check they fit together
#
# Alan W, Mathstream LLC, January 2023
#

from abc import ABC, abstractmethod

from simbywire.config.rm_steps import RmStepBase

try:
    from AirSim import AirSim
except ImportError:
    AirSim = None


class RmStep(RmStepBase, ABC):
    requires: list[str] = []
    """
    A list of things that this RM step requires before it can be run.

    This allows the driver to check that the flow is correct. For example, if
    forecasting produces "leg_forecast" but optimization requires "path_forecast"
    then an exception will be thrown.
    """

    produces: list[str] = []
    """
    A list of things this RM step produces, which may be required by later steps.

    This allows the driver to check that the flow is correct. For example, if
    forecasting produces "leg_forecast" but optimization requires "path_forecast"
    then an exception will be thrown.
    """

    debug_filters: list[str] = []

    def __str__(self):
        return f"RM Step {self.__class__.__name__}: {super().__str__()}"

    @abstractmethod
    def run(
        self, sim: AirSim, airline: str, dcp_index: int, dcp: int, debug: bool = False
    ):
        """This is where the magic happens.

        Every RM step implementation must override this method to do whatever it
        is going to do.
        """
