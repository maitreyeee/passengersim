from simbywire import Simulation, demo_network
from simbywire.config import AirSimConfig
from simbywire.summary import SummaryTables


def test_3mkt(data_regression):
    input_file = demo_network("3mkt")
    sim = Simulation.from_yaml(input_file)
    summary = sim.run(log_reports=False)
    data_regression.check(summary.to_records())


def test_3mkt_alt(data_regression):
    cfg0 = AirSimConfig.from_yaml(demo_network("3mkt"))
    cfg1 = AirSimConfig.from_yaml(demo_network("3mkt-alt"))
    assert cfg0.model_dump() == cfg1.model_dump()


def test_3mkt_2carrier(data_regression):
    input_file = demo_network("3mkt-2carrier")
    sim = Simulation.from_yaml(input_file)
    summary = sim.run(log_reports=False)
    assert isinstance(summary, SummaryTables)
    # TODO enable check when/if stable results can be created
    # data_regression.check(summary.to_records())
