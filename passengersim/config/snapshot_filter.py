import pathlib
from typing import Literal

from pydantic import BaseModel, field_validator


class SnapshotFilter(BaseModel, validate_assignment=True):
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
    directory: pathlib.Path | None = None

    @field_validator("sample", "dcp", "orig", "dest", "flt_no", mode="before")
    def _allow_singletons(cls, v):
        """Allow a singleton value that is converted to a list of one item."""
        if not isinstance(v, list | tuple):
            v = [v]
        return v

    def filepath(self, sim, leg=None, path=None) -> pathlib.Path | None:
        if self.directory is None:
            return None
        pth = self.directory
        if leg is not None:
            pth = pth.joinpath(f"carrier-{leg.carrier}")
        pth = pth.joinpath(f"dpc-{sim.last_dcp}")
        if leg is not None:
            pth = pth.joinpath(f"orig-{leg.orig}")
        elif path is not None:
            pth = pth.joinpath(f"orig-{path.orig}")
        if leg is not None:
            pth = pth.joinpath(f"dest-{leg.dest}")
        elif path is not None:
            pth = pth.joinpath(f"dest-{path.dest}")
        if leg is not None:
            pth = pth.joinpath(f"fltno-{leg.flt_no}")
        elif path is not None:
            pth = pth.joinpath(f"fltno-{path.get_leg_fltno(0)}")
        pth = pth.joinpath(f"sample-{sim.sample}")
        pth.parent.mkdir(parents=True, exist_ok=True)
        return pth.with_suffix(".log")

    def run(self, sim, leg=None, path=None, why=False):
        # Check the filter conditions
        info = ""
        if len(self.sample) > 0 and sim.sample not in self.sample:
            if why:
                print(f" cause {sim.sample}")
            return False
        info += f"  sample={sim.sample}"

        if len(self.dcp) > 0 and sim.last_dcp not in self.dcp:
            if why:
                print(f" cause {sim.last_dcp=}")
            return False
        info += f"  dcp={sim.last_dcp}"

        if leg is not None:
            if self.airline and leg.carrier != self.airline:
                if why:
                    print(f" cause {leg.carrier=}")
                return False
            info += f"  carrier={leg.carrier}"

            if len(self.orig) > 0 and leg.orig not in self.orig:
                if why:
                    print(f" cause {leg.orig=}")
                return False
            info += f"  orig={leg.orig}"

            if len(self.dest) > 0 and leg.dest not in self.dest:
                if why:
                    print(f" cause {leg.dest=}")
                return False
            info += f"  dest={leg.dest}"

            if len(self.flt_no) > 0 and leg.flt_no not in self.flt_no:
                if why:
                    print(f" cause {leg.flt_no=}")
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
            print(f"{self.title}:{info}", flush=True)

        self._last_run_info = info

        if self.type in ["leg_untruncation", "path_untruncation"]:
            return (
                True  # We have a match but, for now, the caller will print the output
            )
        elif self.type == "forecast":
            return True  # Haven't decided on the approach to this yet
        elif self.type == "rm":
            leg.print_bucket_detail()
        elif self.type == "pro_bp":
            return self.filepath(sim, leg, path) or True
        if why:
            print(" cause EOF")
