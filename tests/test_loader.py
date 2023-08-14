import gzip
import io
from pathlib import Path

import pytest
import yaml
from AirSim.airline import ForecastStep, UntruncationStep
from pydantic import ValidationError

from passengersim import AirSimConfig


def test_rm_systems():
    demo1 = """
    rm_systems:
      - name: SystemA
        steps:
        - step_type: untruncation
          name: foo
          algorithm: bar
        - step_type: forecast
          name: baz
          algorithm: exp_smoothing
          alpha: 0.42
      - name: SystemB
        steps:
        - step_type: forecast
          name: baz
          algorithm: additive_pickup
    """
    content = yaml.safe_load(io.StringIO(demo1))
    loaded = AirSimConfig.model_validate(content)

    system0 = loaded.rm_systems["SystemA"]
    assert system0.name == "SystemA"
    assert len(system0.steps) == 2
    assert isinstance(system0.steps[0], UntruncationStep)
    assert isinstance(system0.steps[1], ForecastStep)

    system1 = loaded.rm_systems["SystemB"]
    assert system1.name == "SystemB"
    assert isinstance(system1.steps[0], ForecastStep)
    assert system1.steps[0].step_type == "forecast"
    assert system1.steps[0].algorithm == "additive_pickup"
    assert system1.steps[0].name == "baz"

    # there are several errors in demo2, the parser finds and reports them all with legible error message
    demo2 = """
    rm_systems:
      - steps:
        - step_type: untruncation_misspelled
          name: foo
          algorithm: bar
        - step_type: forecast
          algorithm_misspelled: spam
          alpha: 0.42
    """
    content = yaml.safe_load(io.StringIO(demo2))
    with pytest.raises(ValidationError):
        loaded = AirSimConfig.model_validate(content)


def test_u10_loader():
    u10_config = Path(__file__).parents[2].joinpath("air-sim/networks/u10-config.yaml")
    if not u10_config.exists():
        pytest.skip("u10-config.yaml not available")
    u10_network = (
        Path(__file__).parents[2].joinpath("air-sim/networks/u10-network.yaml.gz")
    )
    if not u10_network.exists():
        pytest.skip("u10-network.yaml.gz not available")
    with open(u10_config) as f:
        content = yaml.safe_load(f)
    with gzip.open(u10_network) as f:
        content.update(yaml.safe_load(f))
    u10 = AirSimConfig.model_validate(content)
    assert len(u10.airlines) == 4
    assert u10.airlines["AL2"].name == "AL2"


# def test_u10_transcoder():
#     sd = SimDriver(
#         input_file=Path(__file__).parents[2].joinpath("networks/u10-airsim.txt"),
#     )
#     sd.loader.dump_network(sd, "/tmp/u10-temp.yml")


# def test_3mkt_transcoder():
#     sd = SimDriver(
#         input_file=Path(__file__).parents[2].joinpath("networks/3mkt-temp.txt"),
#     )
#     sd.loader.dump_network(sd, "/tmp/3mkt.yaml")
