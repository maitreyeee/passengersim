from passengersim.config import SnapshotFilter  # noqa


def apply_snapshot_filters(
    sim,
    filters: list[SnapshotFilter] | None = None,
    only_type=None,
    break_on_first=True,
    leg=None,
    path=None,
):
    # resolve down from Simulation to SimulationEngine
    if hasattr(sim, "sim"):
        sim = sim.sim

    triggered = False
    if filters:
        snapshot_filters = filters
    else:
        snapshot_filters = sim.snapshot_filters
    if snapshot_filters:
        for sf in snapshot_filters:
            if only_type is not None:
                if sf.type == only_type and sf.run(sim, leg=leg, path=path):
                    triggered = True
                    if break_on_first:
                        break
            else:
                if sf.run(sim, leg=leg, path=path):
                    triggered = True
                    if break_on_first:
                        break
    return triggered
