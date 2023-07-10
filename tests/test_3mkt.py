import pathlib

from simbywire import Simulation


def test_3mkt():
    input_file = pathlib.Path(__file__).parents[1].joinpath("networks/3mkt.yaml")
    sim = Simulation.from_yaml(input_file)
    sim.run()
