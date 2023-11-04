# Database

The default data storage solution for PassengerSim is a
[SQLite](https://www.sqlite.org) database file.  The following tables are created when
running a simulation:

| Table                                             | Description                                                                   |
|:--------------------------------------------------|:------------------------------------------------------------------------------|
| [leg_defs](leg_defs.md)                           | Static data about network legs                                                |
| [leg_detail](leg_detail.md)                       | Simulation data at the leg level                                              |
| [leg_bucket_detail](leg_bucket_detail.md)         | Simulation data at the leg-bucket level                                       |
| [path_class_detail](path_class_detail.md)         | Simulation data at the path-class level                                       |
| [demand_detail](demand_detail.md)                 | Simulation data at the demand level                                           |
| [fare_detail](fare_detail.md)                     | Simulation data at the fare level                                             |
| [bookings_by_timeframe](bookings_by_timeframe.md) | Aggregate summary simulation data on bookings by timeframe and bookings class |
