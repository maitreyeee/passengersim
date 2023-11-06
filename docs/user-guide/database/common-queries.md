# Common Queries

PassengerSim has a number of pre-packaged functions that query the database of
results to provide useful summary tables.

| Query                                                                                 | Description                                                           |
|:--------------------------------------------------------------------------------------|:----------------------------------------------------------------------|
| [`bid_price_history`][passengersim.database.common_queries.bid_price_history]         | Compute average bid price history over all legs for each carrier      |
| [`bookings_by_timeframe`][passengersim.database.common_queries.bookings_by_timeframe] | Average bookings and revenue by carrier, booking class, and timeframe |
| [`carrier_history`][passengersim.database.common_queries.carrier_history]             | Sample-level details of carrier-level measures                        |
| [`demand_to_come`][passengersim.database.common_queries.demand_to_come]               | Demand by market and timeframe across each sample                     |
| [`fare_class_mix`][passengersim.database.common_queries.fare_class_mix]               | Fare class mix by carrier                                             |
| [`leg_forecasts`][passengersim.database.common_queries.leg_forecasts]                 | Average forecasts of demand by leg, bucket, and days to departure     |
| [`local_and_flow_yields`][passengersim.database.common_queries.local_and_flow_yields] | Yields for local (nonstop) and flow (connecting) passengers by leg    |
| [`od_fare_class_mix`][passengersim.database.common_queries.od_fare_class_mix]         | Fare class mix by carrier for a particular origin-destination market  |
| [`path_forecasts`][passengersim.database.common_queries.path_forecasts]               | Average forecasts of demand by path, class, and days to departure     |
| [`total_demand`][passengersim.database.common_queries.total_demand]                   | Average total demand                                                  |
