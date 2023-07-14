import pathlib

from simbywire import Simulation


def test_3mkt(data_regression):
    input_file = pathlib.Path(__file__).parents[1].joinpath("networks/3mkt.yaml")
    sim = Simulation.from_yaml(input_file)
    summary = sim.run(log_reports=False)
    summary = {k: v.to_dict(orient='records') for (k,v) in summary.items()}
    data_regression.check(summary)
