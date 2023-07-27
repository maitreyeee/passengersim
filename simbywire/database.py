#
# Utilities for reading and writing AirSim data
# Uses SQLITE
#
import logging
import sqlite3
import string
from datetime import datetime
from pathlib import Path

from AirSim import AirSim

logger = logging.getLogger(__name__)


def get_database_connection(engine="sqlite", filename=None, pragmas=()):
    if engine == "none" or engine is None:
        return None

    elif engine == "mysql":
        raise NotImplementedError

    elif engine == "sqlite":
        if filename is None:
            return None
        if filename != ":memory:":
            Path(filename).parent.mkdir(exist_ok=True, parents=True)
        logger.info(f"connecting to sqlite via sqlite3: {filename}")
        conn = sqlite3.Connection(filename)
        from AirSim.database import initialize_tables

        logger.info("initializing sqlite tables")
        initialize_tables(conn)
        for pragma in pragmas:
            conn.execute(f"PRAGMA {pragma};")
        # maybe faster?
        # cnx.execute("PRAGMA journal_mode = MEMORY;")
        # cnx.execute("PRAGMA synchronous = 0;")
        # cnx.execute("PRAGMA cache_size = 1000000;")
        # cnx.execute("PRAGMA locking_mode = EXCLUSIVE;")
        # cnx.execute("PRAGMA temp_store = MEMORY;")
        return conn

    else:
        raise ValueError(f"{engine=}")


def compute_rrd(sim: AirSim, dep_time: float):
    tmp = int(dep_time / 86400) * 86400
    rrd = int((tmp - sim.last_event_time) / 86400)
    if sim.num_events() == 0:
        rrd = 0
    return rrd


def delete_experiment(cnx: sqlite3.Connection, name):
    with cnx:
        logger.info(f"deleting existing scenario {name!r} from database")
        cnx.execute(f"DELETE FROM leg_detail WHERE scenario = '{name}' ")
        cnx.execute(f"DELETE FROM leg_bucket_detail WHERE scenario = '{name}' ")
        cnx.execute(f"DELETE FROM demand_detail WHERE scenario = '{name}' ")
        cnx.execute(f"DELETE FROM fare WHERE scenario = '{name}' ")


n_commit = 0


# Save details, can be done at each RRD/DCP and at the end of the run
def save_details(cnx: sqlite3.Connection, sim: AirSim, dcp: int):
    global n_commit
    if n_commit == 0:
        cnx.execute("BEGIN TRANSACTION;")
    if not sim.save_timeframe_details and dcp > 0:
        return
    save_demand_multi(cnx, sim, dcp)
    for leg in sim.legs:
        save_leg(cnx, sim, leg, dcp)
        leg.write_to_sqlite(cnx, sim, dcp)
        break
    save_fare_multi(cnx, sim, dcp)
    n_commit += 1
    if n_commit % 50 == 0:
        cnx.execute("END TRANSACTION;")
        cnx.execute("BEGIN TRANSACTION;")


def sql_placeholders(cnx, n):
    if isinstance(cnx, sqlite3.Connection):
        x = "?"
    else:
        x = "%s"
    return ", ".join(x for _ in range(n))


# TODO - How to model RRD / capture date?
def save_leg(cnx, sim, leg, dcp) -> string:
    dep_time = datetime.utcfromtimestamp(leg.dep_time).strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor = cnx.cursor()
        sql = f"""INSERT INTO leg_detail
                (scenario, iteration, trial, sample, rrd, carrier, orig,
                 dest, flt_no, dep_date, capacity, sold, revenue)
                VALUES ({sql_placeholders(cnx, 13)})"""
        cursor.execute(
            sql,
            (
                sim.name,
                sim.iteration,
                sim.trial,
                sim.sample,
                dcp,
                leg.carrier,
                leg.orig,
                leg.dest,
                leg.flt_no,
                dep_time,
                leg.capacity,
                leg.sold,
                leg.revenue,
            ),
        )
        return True
    except Exception as err:
        print(f"Doh !!! leg_detail: {err}")
        return False


# leg_bucket_sql = {}
# def save_leg_bucket_multi(cnx: sqlite3.Connection, sim: AirSim, leg, dcp, commit=True) -> string:
#     dep_time = datetime.utcfromtimestamp(leg.dep_time).strftime('%Y-%m-%d %H:%M:%S')
#     # print("dep_time = ", dep_time)
#     try:
#         cursor = cnx.cursor()
#         cnx_type = type(cnx).__name__
#         if cnx_type not in leg_bucket_sql:
#             sql = leg_bucket_sql[cnx_type] = f"""INSERT INTO leg_bucket_detail
#                 (scenario, iteration, trial, sample, rrd, carrier, orig, dest, flt_no,
#                 dep_date, bucket_number, name, auth, revenue, sold, untruncated_demand,
#                 demand_fcst) VALUES ({sql_placeholders(cnx, 17)})"""
#         else:
#             sql = leg_bucket_sql.get(cnx_type)
#         data_list = []
#         for n, bkt in enumerate(leg.buckets):
#             data = (sim.name, sim.iteration, sim.trial, sim.sample, dcp,
#                     leg.carrier, leg.orig, leg.dest, leg.flt_no, dep_time, n,
#                     bkt.name, bkt.alloc, bkt.revenue, bkt.sold, bkt.untruncated_demand, bkt.fcst_mean)
#             data_list.append(data)
#
#         cursor.executemany(sql, data_list)
#         if commit:
#             cnx.commit()
#         cursor.close()
#         return True
#     except Exception as err:
#         print("Doh !!! leg_bucket_detail: {}".format(err))
#         return False


def save_demand_multi(cnx: sqlite3.Connection, sim: AirSim, dcp) -> string:
    data_list = []
    for dmd in sim.demands:
        data_list.append(
            (
                sim.name,
                sim.iteration,
                sim.trial,
                sim.sample,
                dcp,
                dmd.orig,
                dmd.dest,
                dmd.segment,
                dmd.scenario_demand,
                dmd.sold,
                dmd.revenue,
            )
        )
        # if dmd.sold > dmd.scenario_demand:
        #     print(f"{dmd.orig=}, {dmd.dest=}, {dmd.segment}, {dmd.sold}, {dmd.scenario_demand}")

    try:
        cursor = cnx.cursor()
        sql = f"""INSERT INTO demand_detail
                (scenario, iteration, trial, sample, rrd, orig, dest, segment, sample_demand, sold, revenue)
                VALUES ({sql_placeholders(cnx, 11)})"""
        cursor.executemany(sql, data_list)
        return True
    except Exception as err:
        print(f"Doh !!! demand_detail: {err}")
        return False


def save_fare_multi(cnx: sqlite3.Connection, sim: AirSim, dcp) -> string:
    data_list = []
    for fare in sim.fares:
        data_list.append(
            (
                sim.name,
                sim.iteration,
                sim.trial,
                sim.sample,
                dcp,
                fare.carrier,
                fare.orig,
                fare.dest,
                fare.booking_class,
                fare.sold,
                fare.sold_business,
                fare.price,
            )
        )
    try:
        cursor = cnx.cursor()
        sql = f"""INSERT INTO fare
                (scenario, iteration, trial, sample, rrd, carrier,
                 orig, dest, booking_class, sold, sold_business, price)
                VALUES ({sql_placeholders(cnx, 12)})"""
        cursor.executemany(sql, data_list)
        return True
    except Exception as err:
        print(f"Doh !!! fare: {err}")
        return False


#
# def get_legs(cnx: sqlite3.Connection, _scenario="PODS 1 Leg", _trial=0, _rrd=0):
#     """Return a collection of legs
#        Mostly used by the airline part of the simulation code"""
#     legs = []
#     sql = """SELECT a.iteration, a.trial, a.sample, a.rrd, a.carrier, a.orig, a.dest, a.flt_no,
#                    a.capacity, a.sold, a.q_demand, a.untruncated_demand,
#                    b.bucket_number, b.name AS bucket_name, b.auth, b.sold, b.revenue
#             FROM leg_detail a
#             JOIN leg_bucket_detail b USING(iteration, trial, sample, rrd, carrier, orig, dest, flt_no)
#             WHERE a.scenario = %s
#               AND a.trial = %s
#               AND a.rrd = %s
#             ORDER BY a.iteration, a.trial, a.sample, a.rrd, a.carrier, a.orig, a.dest, a.flt_no, b.bucket_number;"""
#     try:
#         cursor = cnx.cursor()
#         cursor.execute(sql, (_scenario, _trial, _rrd))
#         old_key = None
#         for iteration, trial, sample, rrd, carrier, orig, dest, flt_no, \
#                 capacity, sold, q_demand, untruncated_demand, \
#                 bucket_number, bucket_name, auth, sold, bkt_revenue in cursor:
#             key = (iteration, trial, sample, rrd, carrier, orig, dest, flt_no)
#             if key != old_key:
#                 tmp_leg = Leg(carrier, flt_no, orig, dest, capacity=capacity)
#                 legs.append(tmp_leg)
#             bkt = Bucket(bucket_name, sold=sold)
#             bkt.revenue = bkt_revenue
#             tmp_leg.add_bucket(bkt)
#             old_key = key
#     except Exception as err:
#         print("Doh !!! get_legs: {}".format(err))
#         return []
#
#     return legs
