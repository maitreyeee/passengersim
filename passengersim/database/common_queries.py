import logging

import pandas as pd

from .database import Database

logger = logging.getLogger("passengersim.database")


def fare_class_mix(
    cnx: Database, scenario: str, burn_samples: int = 100
) -> pd.DataFrame:
    qry = """
    SELECT carrier, booking_class,
           (AVG(sold)) AS avg_sold,
           (AVG(revenue)) AS avg_revenue,
           (AVG(revenue) / AVG(sold)) AS avg_price,
           SUM(nobs) AS nobs
    FROM (
            SELECT
                trial, scenario, carrier, booking_class,
                SUM(sold) AS sold,
                SUM(sold * price) AS revenue,
                COUNT(*) AS nobs
            FROM
                fare_detail
            WHERE
                rrd = 0
                AND sample >= ?2
                AND scenario = ?1
            GROUP BY
                trial, sample, carrier, booking_class
    ) tmp
    GROUP BY carrier, booking_class
    ORDER BY carrier, booking_class;
    """
    return cnx.dataframe(qry, (scenario, burn_samples))


def od_fare_class_mix(
    cnx: Database, orig: str, dest: str, scenario: str, burn_samples: int = 100
) -> pd.DataFrame:
    """Get the fare class mix for a particular market."""
    qry = """
    SELECT carrier, booking_class,
           (AVG(sold)) AS avg_sold,
           (AVG(revenue)) AS avg_revenue,
           (AVG(revenue) / AVG(sold)) AS avg_price,
           SUM(nobs) AS nobs
    FROM (
            SELECT
                trial, scenario, carrier, booking_class,
                SUM(sold) AS sold,
                SUM(sold * price) AS revenue,
                COUNT(*) AS nobs
            FROM
                fare_detail
            WHERE
                rrd = 0
                AND sample >= ?2
                AND scenario = ?1
                AND orig = ?3
                AND dest = ?4
            GROUP BY
                trial, sample, carrier, booking_class
    ) tmp
    GROUP BY carrier, booking_class
    ORDER BY carrier, booking_class;
    """
    return cnx.dataframe(qry, (scenario, burn_samples, orig, dest))


def load_factors(cnx: Database, scenario: str, burn_samples: int = 100) -> pd.DataFrame:
    qry = """
    SELECT carrier,
           ROUND(AVG(sold)) AS avg_sold,
           ROUND(AVG(100.0 * sold / cap), 2) AS avg_lf,
           ROUND(AVG(100.0 * rpm / asm), 2) AS sys_lf,
           ROUND(AVG(revenue), 2) AS avg_rev,
           ROUND(AVG(revenue / asm), 3) AS yield,
           ROUND(AVG(revenue) / AVG(sold)) AS avg_price,
           COUNT(*) AS n_obs
    FROM (SELECT trial, sample, carrier,
                 SUM(sold) AS sold,
                 SUM(capacity) AS cap,
                 SUM(sold * distance) AS rpm,
                 SUM(capacity * distance) AS asm,
                 SUM(revenue) AS revenue
          FROM leg_detail
                   JOIN leg_defs USING (flt_no)
          WHERE rrd = 0
            AND sample >= ?2
            AND scenario = ?1
          GROUP BY trial, sample, carrier
         ) tmp
    GROUP BY carrier
    """
    return cnx.dataframe(qry, (scenario, burn_samples))


def total_demand(cnx: Database, scenario: str, burn_samples: int = 100) -> float:
    qry = """
    SELECT AVG(sample_demand)
    FROM (
        SELECT
            trial, sample, SUM(sample_demand) AS sample_demand
        FROM
            demand_detail
        WHERE
            rrd = 0
            AND sample >= ?2
            AND scenario = ?1
        GROUP BY
            trial, sample) tmp;
    """
    return cnx.dataframe(qry, (scenario, burn_samples)).iloc[0, 0]


def bookings_by_timeframe(
    cnx: Database,
    scenario: str,
    from_fare_detail: bool = False,
    burn_samples=100,
) -> pd.DataFrame:
    qry_fare = """
    SELECT trial, carrier, booking_class AS class, rrd,
           (AVG(sold)) AS avg_sold,
           (AVG(sold_business)) AS avg_business,
           (AVG(sold_leisure)) AS avg_leisure,
           (AVG(revenue)) AS avg_revenue,
           (AVG(revenue) / AVG(sold)) AS avg_price,
           (SUM(sold)) AS tot_sold
    FROM (SELECT trial, scenario, carrier, booking_class, rrd,
                 SUM(sold) AS sold,
                 SUM(sold_business) AS sold_business,
                 SUM(sold - sold_business) AS sold_leisure,
                 SUM(sold * price) AS revenue
          FROM fare_detail
          WHERE
                sample >= ?2
                AND scenario = ?1
          GROUP BY trial, sample, carrier, booking_class, rrd) a
    GROUP BY carrier, booking_class, rrd, trial
    ORDER BY carrier, booking_class, rrd, trial;
    """

    if from_fare_detail:
        return cnx.dataframe(qry_fare, (scenario, burn_samples))

    qry_bookings = """
    SELECT
        trial,
        carrier,
        booking_class AS class,
        rrd,
        avg_sold,
        avg_business,
        avg_leisure,
        avg_revenue,
        avg_price
    FROM
        bookings_by_timeframe
    WHERE
        scenario = ?1
    GROUP BY
        carrier, booking_class, rrd, trial
    ORDER BY
        carrier, booking_class, rrd, trial;
    """

    return cnx.dataframe(qry_bookings, (scenario,))


def avg_leg_forecasts(cnx: Database, scenario: str, burn_samples: int = 100):
    qry = """
    SELECT
        carrier,
        flt_no,
        bucket_number,
        name as booking_class,
        rrd,
        AVG(demand_fcst) as demand_fcst
    FROM
        leg_bucket_detail
    WHERE
        scenario = ?1
        AND sample >= ?2
    GROUP BY
        carrier, flt_no, bucket_number, name, rrd
    """
    return cnx.dataframe(
        qry,
        (
            scenario,
            burn_samples,
        ),
    )
