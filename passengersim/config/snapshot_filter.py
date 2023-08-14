import logging
from typing import Literal

from pydantic import BaseModel, field_validator


class SnapshotFilter(BaseModel):
    type: Literal[
        "forecast", "leg_untruncation", "path_untruncation", "rm", "pro_bp", None
    ] = None
    title: str = ""
    airline: str = ""
    sample: list[int] = []
    dcp: list[int] = []
    orig: list[str] = []
    dest: list[str] = []
    flt_no: list[int] = []
    logger: str | None = None

    @field_validator("sample", "dcp", "orig", "dest", "flt_no", mode="before")
    def _allow_singletons(cls, v):
        """Allow a singleton value that is converted to a list of one item."""
        if not isinstance(v, list | tuple):
            v = [v]
        return v

    def run(self, sim, leg=None, path=None):
        # Check the filter conditions
        info = ""
        if len(self.sample) > 0 and sim.sample not in self.sample:
            return False
        info += f"  sample={sim.sample}"

        if len(self.dcp) > 0 and sim.last_dcp not in self.dcp:
            return False
        info += f"  dcp={sim.last_dcp}"

        if leg is not None:
            if len(self.orig) > 0 and leg.orig not in self.orig:
                return False
            info += f"  orig={leg.orig}"

            if len(self.dest) > 0 and leg.dest not in self.dest:
                return False
            info += f"  dest={leg.dest}"

            if len(self.flt_no) > 0 and leg.flt_no not in self.flt_no:
                return False
            info += f"  flt_no={leg.flt_no}"

        if path is not None:
            if len(self.orig) > 0 and path.orig not in self.orig:
                return False
            info += f"  orig={path.orig}"

            if len(self.dest) > 0 and path.dest not in self.dest:
                return False
            info += f"  dest={path.dest}"

            if len(self.flt_no) > 0 and path.get_leg_fltno(0) not in self.flt_no:
                return False
            info += f"  flt_no={path.get_leg_fltno(0)}"

        # Now do something
        if len(self.title) > 0:
            if self.logger:
                logging.getLogger(self.logger)
            print(f"{self.title}:{info}")

        if self.type in ["leg_untruncation", "path_untruncation"]:
            return (
                True  # We have a match but, for now, the caller will print the output
            )
        elif self.type == "forecast":
            pass  # Haven't decided on the approach to this yet
        elif self.type == "rm":
            leg.print_bucket_detail()
        elif self.type == "pro_bp":
            return True
