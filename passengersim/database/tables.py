from __future__ import annotations

from collections.abc import Iterable

from .database import Database


def create_table_legs(cnx: Database, legs: Iterable | None = None):
    sql = """
    CREATE TABLE IF NOT EXISTS leg_defs
    (
        flt_no INTEGER PRIMARY KEY,
        carrier TEXT,
        orig TEXT,
        dest TEXT,
        dep_time INTEGER,
        arr_time INTEGER,
        capacity INTEGER,
        distance FLOAT
    );
    """
    cnx.execute(sql)
    for leg in legs:
        cnx.execute(
            """
            INSERT OR REPLACE INTO leg_defs(
                flt_no,
                carrier,
                orig,
                dest,
                dep_time,
                arr_time,
                capacity,
                distance
            ) VALUES (
                ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8
            )
            """,
            (
                leg.flt_no,
                leg.carrier,
                leg.orig,
                leg.dest,
                leg.dep_time,
                leg.arr_time,
                leg.capacity,
                leg.distance,
            ),
        )


def create_table_leg_detail(cnx: Database, primary_key: bool = False):
    sql = """
    CREATE TABLE IF NOT EXISTS leg_detail
    (
        scenario	    	VARCHAR(20) NOT NULL,
        iteration	    	INT NOT NULL,
        trial	        	INT NOT NULL,
        sample  	    	INT NOT NULL,
        rrd             	INT NOT NULL,
        flt_no		    	INT NOT NULL,
        updated_at	    	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        sold	    		INT,
        revenue             FLOAT,
        q_demand            FLOAT,
        untruncated_demand  FLOAT,
        demand_fcst         FLOAT
        {primary_key}
    );
    """
    if primary_key is True:
        sql = sql.format(
            primary_key=", PRIMARY KEY(scenario, iteration, trial, sample, carrier, orig, dest, flt_no, rrd, dep_date)"
        )
    else:
        sql = sql.format(primary_key="")
    cnx.execute(sql)


def create_table_leg_bucket_detail(cnx: Database, primary_key: bool = False):
    sql = """
    CREATE TABLE IF NOT EXISTS leg_bucket_detail
    (
        scenario		VARCHAR(20) NOT NULL,
        iteration		INT NOT NULL,
        trial	    	INT NOT NULL,
        sample  		INT NOT NULL,
        rrd         	INT NOT NULL,
        carrier			VARCHAR(10) NOT NULL,
        orig			VARCHAR(10) NOT NULL,
        dest			VARCHAR(10) NOT NULL,
        flt_no			INT NOT NULL,
        dep_date		DATETIME NOT NULL,
        bucket_number   INT NOT NULL,
        name            VARCHAR(10) NOT NULL,
        auth    		INT,
        revenue    		FLOAT,
        sold			INT,
        untruncated_demand     FLOAT,
        demand_fcst     FLOAT,
        updated_at		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        {primary_key}
    );
    """
    if primary_key is True:
        sql = sql.format(
            primary_key=", PRIMARY KEY(scenario, iteration, trial, sample, rrd, "
            "carrier, orig, dest, flt_no, dep_date, bucket_number)"
        )
    else:
        sql = sql.format(primary_key="")
    cnx.execute(sql)


def create_table_demand_detail(cnx: Database, primary_key: bool = False):
    sql = """
    CREATE TABLE IF NOT EXISTS demand_detail
    (
        scenario		VARCHAR(20) NOT NULL,
        iteration		INT NOT NULL,
        trial	    	INT NOT NULL,
        sample  		INT NOT NULL,
        rrd     	    INT NOT NULL,
        segment			VARCHAR(10) NOT NULL,
        orig			VARCHAR(10) NOT NULL,
        dest			VARCHAR(10) NOT NULL,
        updated_at		DATETIME NOT NULL DEFAuLT CURRENT_TIMESTAMP,
        sample_demand   FLOAT,
        sold			INT,
        no_go			INT,
        revenue			FLOAT
        {primary_key}
    );
    """
    if primary_key is True:
        sql = sql.format(
            primary_key=", PRIMARY KEY(scenario, iteration, trial, sample, rrd, segment, orig, dest)"
        )
    else:
        sql = sql.format(primary_key="")
    cnx.execute(sql)


def create_table_fare_detail(cnx: Database, primary_key: bool = False):
    sql = """
    CREATE TABLE IF NOT EXISTS fare_detail
    (
        scenario		VARCHAR(20) NOT NULL,
        iteration		INT NOT NULL,
        trial	    	INT NOT NULL,
        sample  		INT NOT NULL,
        rrd       		INT NOT NULL,
        carrier			VARCHAR(10) NOT NULL,
        orig			VARCHAR(10) NOT NULL,
        dest			VARCHAR(10) NOT NULL,
        booking_class   VARCHAR(10) NOT NULL,
        sold			INT,
        sold_business	INT,
        price           FLOAT,
        updated_at		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        {primary_key}
    );
    """
    if primary_key is True:
        sql = sql.format(
            primary_key=", PRIMARY KEY(scenario, iteration, trial, sample, rrd, carrier, orig, dest, booking_class)"
        )
    else:
        sql = sql.format(primary_key="")
    cnx.execute(sql)


def create_table_bookings_by_timeframe(cnx: Database, primary_key: bool = False):
    sql = """
    CREATE TABLE IF NOT EXISTS bookings_by_timeframe
    (
        scenario		VARCHAR(20) NOT NULL,
        carrier			VARCHAR(10) NOT NULL,
        booking_class   VARCHAR(10) NOT NULL,
        rrd       		INT NOT NULL,
        tot_sold		FLOAT,
        avg_sold		FLOAT,
        avg_business	FLOAT,
        avg_leisure     FLOAT,
        avg_revenue     FLOAT,
        avg_price       FLOAT,
        updated_at		DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        {primary_key}
    );
    """
    if primary_key is True:
        sql = sql.format(
            primary_key=", PRIMARY KEY(scenario, carrier, booking_class, rrd)"
        )
    else:
        sql = sql.format(primary_key="")
    cnx.execute(sql)


def create_table_booking_curve(cnx: Database, primary_key: bool = True):
    sql = """
    CREATE TABLE IF NOT EXISTS booking_curve (
        scenario		VARCHAR(20) NOT NULL,
        carrier			VARCHAR(10) NOT NULL,
        orig			VARCHAR(10) NOT NULL,
        dest			VARCHAR(10) NOT NULL,
        flt_no			INT NOT NULL,
        rrd         	INT NOT NULL,
        ratio           FLOAT NOT NULL
        {primary_key}
    );
    """
    if primary_key is True:
        sql = sql.format(
            primary_key=", PRIMARY KEY(scenario, carrier, orig, dest, flt_no, rrd)"
        )
    else:
        sql = sql.format(primary_key="")
    cnx.execute(sql)


def create_table_distance(cnx: Database, primary_key: bool = True):
    sql = """
    CREATE TABLE IF NOT EXISTS distance (
        orig			VARCHAR(10) NOT NULL,
        dest			VARCHAR(10) NOT NULL,
        miles           FLOAT
        {primary_key}
    );
    """
    if primary_key is True:
        sql = sql.format(primary_key=", PRIMARY KEY(orig, dest)")
    else:
        sql = sql.format(primary_key="")
    cnx.execute(sql)


def create_tables(cnx: Database, primary_keys: dict[str, bool] | None = None):
    pk = dict(
        leg=False,
        leg_bucket=False,
        demand=False,
        fare=False,
        booking_curve=True,
        distance=True,
        bookings=False,
    )
    if primary_keys is not None:
        pk.update(primary_keys)
    create_table_leg_detail(cnx, pk["leg"])
    create_table_leg_bucket_detail(cnx, pk["leg_bucket"])
    create_table_demand_detail(cnx, pk["demand"])
    create_table_fare_detail(cnx, pk["fare"])
    create_table_bookings_by_timeframe(cnx, pk["bookings"])
    create_table_booking_curve(cnx, pk["booking_curve"])
    create_table_distance(cnx, pk["distance"])
    cnx._commit_raw()
