import pandas as pd

from .database import Database


def fare_class_mix(cnx: Database, scenario: str) -> pd.DataFrame:
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
                AND sample > 100
                AND scenario = ?1
            GROUP BY
                trial, sample, carrier, booking_class
    ) tmp
    GROUP BY carrier, booking_class
    ORDER BY carrier, booking_class;
    """
    return cnx.dataframe(qry, (scenario,))


def load_factors(cnx: Database, scenario: str) -> pd.DataFrame:
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
                 SUM(sold * d.miles) AS rpm,
                 SUM(capacity * d.miles) AS asm,
                 SUM(revenue) AS revenue
          FROM leg_detail a
                   JOIN distance d USING (orig, dest)
          WHERE rrd = 0
            AND sample > 100
            AND scenario = ?1
          GROUP BY trial, sample, carrier
         ) tmp
    """
    return cnx.dataframe(qry, (scenario,))


def total_demand(cnx: Database, scenario: str) -> float:
    qry = """
    SELECT AVG(sample_demand)
    FROM (
        SELECT
            trial, sample, SUM(sample_demand) AS sample_demand
        FROM
            demand_detail
        WHERE
            rrd = 0
            AND sample > 100
        GROUP BY
            trial, sample) tmp;
    """
    return cnx.dataframe(qry, (scenario,)).iloc[0, 0]


def bookings_by_timeframe(
    cnx: Database,
    scenario: str,
    from_fare_detail: bool = False,
    burn_samples=100,
) -> pd.DataFrame:
    qry_fare = """
    SELECT carrier, booking_class AS class, rrd,
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
    GROUP BY carrier, booking_class, rrd
    ORDER BY carrier, booking_class, rrd;
    """

    if from_fare_detail:
        return cnx.dataframe(qry_fare, (scenario, burn_samples))

    qry_bookings = """
    SELECT
        carrier,
        booking_class AS class,
        rrd,
        avg_sold,
        avg_business,
        avg_leisure,
        avg_revenue,
        avg_price,
        tot_sold
    FROM
        bookings_by_timeframe
    WHERE
        scenario = ?1
    ORDER BY
        carrier, booking_class, rrd;
    """

    return cnx.dataframe(qry_bookings, (scenario,))
