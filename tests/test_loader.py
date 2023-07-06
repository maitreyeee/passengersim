import io
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from simbywire import AirSimConfig
from simbywire.config.rm_systems import ForecastStep, UntruncationStep


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
          algorithm: spam
          alpha: 0.42
      - name: SystemB
        steps:
        - step_type: forecast
          name: baz
          algorithm: spam
    """
    content = yaml.safe_load(io.StringIO(demo1))
    loaded = AirSimConfig.model_validate(content)

    system0 = loaded.rm_systems[0]
    assert system0.name == "SystemA"
    assert len(system0.steps) == 2
    assert isinstance(system0.steps[0], UntruncationStep)
    assert isinstance(system0.steps[1], ForecastStep)

    system1 = loaded.rm_systems[1]
    assert system1.name == "SystemB"
    assert isinstance(system1.steps[0], ForecastStep)
    assert system1.steps[0].step_type == "forecast"
    assert system1.steps[0].algorithm == "spam"
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
    u10_yaml = Path(__file__).parents[2].joinpath("networks/u10.yaml")
    with open(u10_yaml) as f:
        content = yaml.safe_load(f)
    AirSimConfig.model_validate(content)
