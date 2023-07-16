import pathlib

from simbywire import Simulation, demo_network


def test_3mkt(data_regression):
    input_file = demo_network("3mkt")
    sim = Simulation.from_yaml(input_file)
    summary = sim.run(log_reports=False)
    summary = {k: v.to_dict(orient='records') for (k,v) in summary._asdict().items()}
    data_regression.check(summary)
