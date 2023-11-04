# Leg Definitions

The `leg_defs` database table stores static details about the legs in the
simulation.  Simulation results at the leg level are stored in the
[`leg_details`](leg_details.md) table instead.

The `leg_defs` table is created by the
[create_table_legs][passengersim.database.tables.create_table_legs] function,
which is called in the [Simulation][passengersim.Simulation] initialization
step, so it should be available and populated for every simulation run.

## Table Schema

| Column    | Data Type           | Description                                        |
|:----------|:--------------------|:---------------------------------------------------|
| flt_no    | INTEGER PRIMARY KEY | Unique identifier for a given leg [^1]             |
| carrier   | TEXT                | Name of carrier for this leg                       |
| orig      | TEXT                | Origin (typically an airport code or similar)      |
| dest      | TEXT                | Destination (typically an airport code or similar) |
| dep_time  | INTEGER             |                                                    |
| arr_time  | INTEGER             |                                                    |
| capacity  | INTEGER             | Number of seats on this leg                        |
| distance	 | FLOAT               | Distance from `orig` to `dest` in miles.           |


[^1]:
    In the "real world" the limitations of current technology make it such that
    flight numbers are not necessary unique by leg, as a single carrier may have
    multiple segments sharing the same flight number, and multiple carriers will
    have completely unrelated flights with the same flight number.  To simplify
    data processing, PassengerSim uses a unique id for every travel segment. Networks
    in PassengerSim that are derived from realistic sources will require some
    modest preprocessing to create unique flight numbers for every leg.
