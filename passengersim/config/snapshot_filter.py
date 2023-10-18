import pathlib
import time
from typing import Literal

from pydantic import BaseModel, field_validator


class SnapshotInstruction:
    def __init__(
        self,
        trigger: bool = False,
        filepath: pathlib.Path | None = None,
        why: str | None = None,
    ):
        self.trigger = bool(trigger)
        """Has this snapshot been triggered."""
        self.why = why
        """Explanation of why snapshot is (or is not) triggered."""
        self.filepath = filepath
        """Where to save snapshot content."""

    def __bool__(self) -> bool:
        return self.trigger

    def write(self, content: str = ""):
        """Write snapshot content to a file, or just print it"""
        if self.filepath:
            with self.filepath.open(mode="w") as f:
                f.write(self.why)
                f.write("\n")
                if isinstance(content, bytes):
                    f.write(content.decode("utf-8"))
                elif isinstance(content, str):
                    f.write(content)
                else:
                    f.write(str(content))
        else:
            print(self.why)
            print(content)

    def write_more(self, content: str = ""):
        """Write additional snapshot content to a file, or just print it"""
        if self.filepath:
            with self.filepath.open(mode="a") as f:
                if isinstance(content, bytes):
                    f.write(content.decode("utf-8"))
                elif isinstance(content, str):
                    f.write(content)
                else:
                    f.write(str(content))
        else:
            print(content)


class SnapshotFilter(BaseModel, validate_assignment=True):
    type: Literal[
        "forecast", "leg_untruncation", "path_untruncation", "rm", "pro_bp", None
    ] = None
    title: str = ""
    airline: str = ""
    trial: list[int] = []
    sample: list[int] = []
    dcp: list[int] = []
    orig: list[str] = []
    dest: list[str] = []
    flt_no: list[int] = []
    logger: str | None = None
    directory: pathlib.Path | None = None

    @field_validator("trial", "sample", "dcp", "orig", "dest", "flt_no", mode="before")
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
        if sim.num_trials > 1:
            pth = pth.joinpath(f"trial-{sim.trial}")
        pth = pth.joinpath(f"sample-{sim.sample}")
        pth.parent.mkdir(parents=True, exist_ok=True)
        return pth.with_suffix(".log")

    def run(
        self, sim, leg=None, path=None, carrier=None, why=False
    ) -> SnapshotInstruction:
        # Check the filter conditions
        info = ""

        if len(self.trial) > 0 and sim.trial not in self.trial and sim.num_trials > 1:
            return SnapshotInstruction(False, why=f"cause {sim.trial=}")
        info += f"  trial={sim.trial}"

        if len(self.sample) > 0 and sim.sample not in self.sample:
            return SnapshotInstruction(False, why=f"cause {sim.sample=}")
        info += f"  sample={sim.sample}"

        if len(self.dcp) > 0 and sim.last_dcp not in self.dcp:
            return SnapshotInstruction(False, why=f"cause {sim.last_dcp=}")
        info += f"  dcp={sim.last_dcp}"

        if leg is not None:
            if self.airline and leg.carrier != self.airline:
                return SnapshotInstruction(False, why=f"cause {leg.carrier=}")
            info += f"  carrier={leg.carrier}"

            if len(self.orig) > 0 and leg.orig not in self.orig:
                return SnapshotInstruction(False, why=f"cause {leg.orig=}")
            info += f"  orig={leg.orig}"

            if len(self.dest) > 0 and leg.dest not in self.dest:
                return SnapshotInstruction(False, why=f"cause {leg.dest=}")
            info += f"  dest={leg.dest}"

            if len(self.flt_no) > 0 and leg.flt_no not in self.flt_no:
                return SnapshotInstruction(False, why=f"cause {leg.flt_no=}")
            info += f"  flt_no={leg.flt_no}"

        if path is not None:
            if len(self.orig) > 0 and path.orig not in self.orig:
                return SnapshotInstruction(False, why=f"cause {path.orig=}")
            info += f"  orig={path.orig}"

            if len(self.dest) > 0 and path.dest not in self.dest:
                return SnapshotInstruction(False, why=f"cause {path.dest=}")
            info += f"  dest={path.dest}"

            if len(self.flt_no) > 0 and path.get_leg_fltno(0) not in self.flt_no:
                return SnapshotInstruction(False, why=f"cause {path.get_leg_fltno(0)=}")
            info += f"  flt_no={path.get_leg_fltno(0)}"

        if carrier is not None:
            if self.airline and carrier != self.airline:
                return SnapshotInstruction(False, why=f"cause {carrier=}")
            info += f"  carrier={carrier}"

        # Now do something
        snapshot_file = self.filepath(sim, leg, path)
        title = f"{self.title}:{info}\n{time.strftime('Snapshot created %Y-%m-%d %A %I:%M:%S %p')}\n"
        if len(self.title) > 0 and not snapshot_file:
            print(f"{self.title}:{info}", flush=True)

        self._last_run_info = info

        if self.type in ["leg_untruncation", "path_untruncation"]:
            return SnapshotInstruction(True, snapshot_file, why=title)
        elif self.type == "forecast":
            return SnapshotInstruction(True, snapshot_file, why=title)
        elif self.type == "rm":
            bucket_detail = leg.print_bucket_detail()
            snapshot_file = self.filepath(sim, leg, path)
            if snapshot_file:
                with snapshot_file.open(mode="a") as f:
                    f.write(title)
                    f.write(bucket_detail)
            else:
                print(bucket_detail)
            return SnapshotInstruction(True, snapshot_file, why=title)
        elif self.type == "pro_bp":
            return SnapshotInstruction(True, snapshot_file, why=title)

        return SnapshotInstruction(False, why="cause unknown")
