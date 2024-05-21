import pathlib

import joblib

from .config import Config
from .driver import BaseSimulation, Simulation
from .summary import SummaryTables


class MultiSimulation(BaseSimulation):
    def __init__(
        self,
        config: Config,
        output_dir: pathlib.Path | None = None,
    ):
        super().__init__(config, output_dir)
        self.config = config
        self._simulators = {}

    def run_trial(self, trial_id: int):
        cfg = self.config.model_copy(deep=True)
        if str(cfg.db.filename) != ":memory:":
            cfg.db.filename = cfg.db.filename.with_suffix(
                f".trial{trial_id:02}" + cfg.db.filename.suffix
            )
        sim = Simulation(cfg, self.output_dir)
        self._simulators[trial_id] = sim
        summary = sim.run(single_trial=trial_id)
        try:
            del summary.cnx
        except AttributeError:
            pass
        return summary

    def run(self):
        with joblib.Parallel(
            n_jobs=self.config.simulation_controls.num_trials
        ) as parallel:
            results = parallel(
                joblib.delayed(self.run_trial)(trial_id)
                for trial_id in range(self.config.simulation_controls.num_trials)
            )
        return SummaryTables.aggregate(results)

    def sequential_run(self):
        results = []
        for trial_id in range(self.config.simulation_controls.num_trials):
            print("starting trial", trial_id)
            results.append(self.run_trial(trial_id))
            print("finished trial", trial_id)
        return SummaryTables.aggregate(results)


# def spin(n):
#     c = cfg.model_copy(deep=True)
#     c.simulation_controls.random_seed = 42 + n
#     c.simulation_controls.num_trials = 1
#     c.simulation_controls.num_samples = 10
#     c.simulation_controls.burn_samples = 5
#     c.db.filename = c.db.filename.with_suffix(f".trial{n:02}" + c.db.filename.suffix)
#     c.simulation_controls.show_progress_bar = False
#     sim = pax.Simulation(c)
#     summary = sim.run()
#     del summary.cnx # cannot pickle DB connection
#     return summary
