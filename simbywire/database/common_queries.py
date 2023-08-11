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
