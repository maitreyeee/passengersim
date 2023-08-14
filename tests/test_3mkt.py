import pytest

from passengersim import Simulation, demo_network
from passengersim.config import AirSimConfig
from passengersim.database.write_demands import save_demand_to_database
from passengersim.summary import SummaryTables


def test_3mkt(data_regression):
    input_file = demo_network("3mkt")
    config = AirSimConfig.from_yaml(input_file)
    config.simulation_controls.num_trials = 1
    config.simulation_controls.num_samples = 10
    config.simulation_controls.burn_samples = 9
    sim = Simulation(config, output_dir=None)
    _summary = sim.run(log_reports=False)
    # data_regression.check(_summary.to_records())


def test_3mkt_alt():
    cfg0 = AirSimConfig.from_yaml(demo_network("3mkt"))
    cfg1 = AirSimConfig.from_yaml(demo_network("3mkt-alt"))
    assert cfg0.model_dump() == cfg1.model_dump()


@pytest.mark.parametrize("fast", [True, False])
def test_3mkt_db_detail(fast):
    input_file = demo_network("3mkt")
    config = AirSimConfig.from_yaml(input_file)

    n_legs = len(config.legs)
    assert n_legs == 9

    n_demands = len(config.demands)
    assert n_demands == 6

    n_fares = len(config.fares)
    assert n_fares == 120

    n_dcps = len(config.dcps) + (1 if (0 not in config.dcps) else 0)
    assert n_dcps == 17

    n_classes = len(config.classes)
    assert n_classes == 10

    num_samples = 20
    config.simulation_controls.num_trials = 1
    config.simulation_controls.num_samples = num_samples
    config.simulation_controls.burn_samples = 10

    config.db.engine = "sqlite"
    config.db.filename = ":memory:"
    config.db.fast = fast
    if "demand" in config.db.write_items:
        # remove demand to test plug in hook
        config.db.write_items.remove("demand")
    config.db.dcp_write_hooks.append(save_demand_to_database)
    config.simulation_controls.write_raw_files = False
    sim = Simulation(config, output_dir=None)
    summary = sim.run(log_reports=False)
    assert summary.demands.shape == (6, 9)
    fares = sim.cnx.dataframe("SELECT * FROM fare_detail")
    assert fares.shape == (num_samples * n_fares * n_dcps, 13)  # 40800
    legs = sim.cnx.dataframe("SELECT * FROM leg_detail")
    assert legs.shape == (num_samples * n_dcps * n_legs, 17)  # 3060
    buckets = sim.cnx.dataframe("SELECT * FROM leg_bucket_detail")
    assert buckets.shape == (num_samples * n_classes * n_dcps * n_legs, 18)  # 30600
    dmds = sim.cnx.dataframe("SELECT * FROM demand_detail")
    assert dmds.shape == (num_samples * n_demands * n_dcps, 13)  # 2040


def test_3mkt_2carrier(data_regression):
    input_file = demo_network("3mkt-2carrier")
    cfg = AirSimConfig.from_yaml(input_file)
    cfg.db.engine = None  # no db connection
    sim = Simulation(cfg)
    summary = sim.run(log_reports=False)
    assert isinstance(summary, SummaryTables)
    # TODO enable check when/if stable results can be created
    # data_regression.check(summary.to_records())
