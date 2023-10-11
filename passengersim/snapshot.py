from passengersim.config import SnapshotFilter, SnapshotInstruction  # noqa


def apply_snapshot_filters(
    sim,
    filters: list[SnapshotFilter] | None = None,
    only_type=None,
    break_on_first=True,
    leg=None,
    path=None,
):
    # deprecated....
    # resolve down from Simulation to SimulationEngine
    if hasattr(sim, "sim"):
        sim = sim.sim

    triggered = False
    if filters:
        snapshot_filters = filters
    else:
        snapshot_filters = sim.snapshot_filters
    filepath = True
    if snapshot_filters:
        for sf in snapshot_filters:
            if only_type is not None:
                if sf.type == only_type:
                    filepath = sf.run(sim, leg=leg, path=path)
                    if filepath:
                        triggered = True
                        if break_on_first:
                            break
            else:
                filepath = sf.run(sim, leg=leg, path=path)
                if filepath:
                    triggered = True
                    if break_on_first:
                        break
    return triggered and filepath


def get_snapshot_instruction(
    sim,
    filters: list[SnapshotFilter] | None = None,
    only_type=None,
    break_on_first=True,
    leg=None,
    path=None,
    carrier=None,
) -> SnapshotInstruction:
    # resolve down from Simulation to SimulationEngine
    if hasattr(sim, "sim"):
        sim = sim.sim

    snapshot_instruction = SnapshotInstruction(False)
    if filters:
        snapshot_filters = filters
    else:
        snapshot_filters = sim.snapshot_filters
    if snapshot_filters:
        for sf in snapshot_filters:
            if only_type is not None:
                if sf.type == only_type:
                    snapshot_instruction = sf.run(
                        sim, leg=leg, path=path, carrier=carrier
                    )
                    if snapshot_instruction and break_on_first:
                        break
            else:
                snapshot_instruction = sf.run(sim, leg=leg, path=path, carrier=carrier)
                if snapshot_instruction and break_on_first:
                    break
    return snapshot_instruction
