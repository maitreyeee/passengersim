# Home

This is the technical documentation for the PassengerSim simulator.

## GT Student Quick-start

1. Double click `create-airsim-env.cmd` in `C:\PyPI-Local` to install your working environment.
2. Look on your desktop for `AirSim-Env.cmd`, double click that to open and use your environment.
3. Inside the `AirSim-Env` window, run the following command to run a simple simulation 
   and confirm it is working.
   ```bat
   python -m AirSim run -n "C:\AirSim-networks\network-3mkt-pods.txt" ^
          -o "%USERPROFILE%\air-sim-outputs" --fast
   ```
   You should then see an "air-sim-outputs" directory in your home directory.  With the `--fast`
   option, the .sqlite file in the output directory is just a stub until the simulation completes, 
   then it is populated all at once with the stored data from that simulation.  This overcomes the 
   very slow file write speeds on this server.

For actual simulation experiments, you'll want to change the `-n` file to the network simulation defs 
that you want to use.  To work with the outputs in Python, see [reading data](./reading-data.ipynb)