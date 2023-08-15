# Counting Simulations

A simulation run consists of a number of independent trials, and each trial is 
made up of a sequence of dependent samples -- earlier samples in a trial are used
to develop forecasts and train optimization algorithms used by carriers in later
samples of the same trial.

The number of trials is set by the 
[`num_trials`][passengersim.config.simulation_controls.SimulationSettings.num_trials]
configuration, and the number of samples in each trial is set by
[`num_samples`][passengersim.config.simulation_controls.SimulationSettings.num_samples].
Both values can be found in the
[`simulation_controls`][passengersim.config.Config.simulation_controls]
configuration inputs.

We can think of a sample as a "typical" departure day.  When generating results, 
the first X samples from each trial as these are during a "burn period" when the 
simulation is getting started and sufficient history is being generated to use 
for forecasts and other steps.  The nuber of samples in the burn period is set by
the [`burn_samples`][passengersim.config.simulation_controls.SimulationSettings.burn_samples] 
configuration value.

