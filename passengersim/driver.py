from __future__ import annotations

import logging
import os
import pathlib
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd

import passengersim.config.rm_systems
import passengersim.core
from passengersim.config import Config
from passengersim.config.snapshot_filter import SnapshotFilter
from passengersim.core import Event, Frat5, PathClass, SimulationEngine
from passengersim.summary import SummaryTables

from . import database
from .progressbar import DummyProgressBar, ProgressBar

logger = logging.getLogger("passengersim")


class Simulation:
    @classmethod
    def from_yaml(
        cls,
        filenames: pathlib.Path | list[pathlib.Path],
        output_dir: pathlib.Path | None = None,
    ):
        config = passengersim.config.Config.from_yaml(filenames)
        return cls(config, output_dir)

    def __init__(
        self,
        config: Config,
        output_dir: pathlib.Path | None = None,
    ):
        if output_dir is None:
            import tempfile

            self._tempdir = tempfile.TemporaryDirectory()
            output_dir = os.path.join(self._tempdir.name, "test1")
        self.cnx = None
        if config.simulation_controls.write_raw_files:
            try:
                from passengersim_core.utils import FileWriter
            except ImportError:
                self.file_writer = None
            else:
                self.file_writer = FileWriter.FileWriter(output_dir)
        else:
            self.file_writer = None
        #        self.dcp_list = [63, 24, 17, 10, 5]
        self.dcp_list = [63, 56, 49, 42, 35, 31, 28, 24, 21, 17, 14, 10, 7, 5, 3, 1, 0]
        self.classes = []
        self.fare_sales_by_dcp = defaultdict(int)
        self.fare_sales_by_airline_dcp = defaultdict(int)
        self.fare_details_sold = defaultdict(int)
        self.fare_details_sold_business = defaultdict(int)
        self.fare_details_revenue = defaultdict(float)
        self.output_dir = output_dir
        self.demand_multiplier = 1.0
        self.airports = []
        self.choice_models = {}
        self.frat5curves = {}
        self.load_factor_curves = {}
        self.debug = False
        self.update_frequency = None
        self.random_generator = passengersim.core.Generator(42)
        self.sample_done_callback = lambda n, n_total: None
        self._initialize(config)
        self.cnx = database.Database(
            engine=config.db.engine,
            filename=config.db.filename,
            pragmas=config.db.pragmas,
            commit_count_delay=config.db.commit_count_delay,
        )
        if self.cnx.is_open:
            database.tables.create_table_legs(self.cnx._connection, self.sim.legs)
            database.tables.create_table_path_defs(self.cnx._connection, self.sim.paths)
            if config.db != ":memory:":
                self.cnx.save_configs(config)

    @property
    def base_time(self) -> int:
        return self.sim.base_time

    @property
    def snapshot_filters(self) -> list[SnapshotFilter] | None:
        try:
            sim = self.sim
        except AttributeError:
            return None
        return sim.snapshot_filters

    @snapshot_filters.setter
    def snapshot_filters(self, x: list[SnapshotFilter]):
        try:
            sim = self.sim
        except AttributeError as err:
            raise ValueError(
                "sim not initialized, cannot set snapshot_filters"
            ) from err
        sim.snapshot_filters = x

    def _initialize(self, config: Config):
        self.sim = passengersim.core.SimulationEngine(name=config.scenario)
        self.sim.config = config
        self.sim.random_generator = self.random_generator
        self.sim.snapshot_filters = config.snapshot_filters
        for pname, pvalue in config.simulation_controls:
            if pname == "demand_multiplier":
                self.demand_multiplier = pvalue
            elif pname == "write_raw_files":
                self.write_raw_files = pvalue
            elif pname == "random_seed":
                self.random_generator.seed(pvalue)
            elif pname == "update_frequency":
                self.update_frequency = pvalue
            elif pname == "base_date":
                pass
            elif pname == "dcp_hour":
                pass
            elif pname == "show_progress_bar":
                pass
            elif pname == "double_capacity_until":
                pass
            elif pname == "timeframe_demand_allocation":
                pass
            elif pname == "tot_z_factor":
                pass
            elif pname == "simple_k_factor":
                pass
            else:
                self.sim.set_parm(pname, float(pvalue))
        for pname, pvalue in config.simulation_controls.model_extra.items():
            print(f"extra simulation setting: {pname} = ", float(pvalue))
            self.sim.set_parm(pname, float(pvalue))

        self.rm_systems = {}
        from passengersim_core.airline.rm_system import Rm_System

        for rm_name, rm_system in config.rm_systems.items():
            x = self.rm_systems[rm_name] = Rm_System(rm_name)
            for process_name, process in rm_system.processes.items():
                step_list = [s._factory() for s in process]
                x.add_process(process_name, step_list)

            ### This needs ot be revisited, now that we have DCP and DAILY step lists
            availability_control = rm_system.availability_control
            processes = (
                rm_system.processes["dcp"] if "dcp" in rm_system.processes else []
            )
            if len(processes) == 0:
                _inferred_availability_control = "none"
            # elif steps[-1].step_type in ("probp", "udp"):
            #    _inferred_availability_control = "bp"
            # else:
            #    _inferred_availability_control = "vn"
            if availability_control == "infer":
                raise NotImplementedError("")
            #   availability_control = _inferred_availability_control
            # else:
            #   if availability_control != _inferred_availability_control:
            #     warnings.warn(
            #         f"availability_control for this RmSystem should be "
            #         f"{_inferred_availability_control} but it is set to "
            #         f"{availability_control}"
            #     )
            x.availability_control = availability_control

        for cm_name, cm in config.choice_models.items():
            x = passengersim.core.ChoiceModel(cm_name, cm.kind)
            for pname, pvalue in cm:
                if pname in ("kind", "name"):
                    continue
                if pvalue is None:
                    continue
                if isinstance(pvalue, list | tuple):
                    x.add_parm(pname, *pvalue)
                else:
                    x.add_parm(pname, pvalue)
            x.random_generator = self.random_generator
            self.choice_models[cm_name] = x

        for f5_name, f5_data in config.frat5_curves.items():
            f5 = Frat5(f5_name)
            for _dcp, val in f5_data.curve.items():
                f5.add_vals(val)
            self.sim.add_frat5(f5)
            self.frat5curves[f5_name] = f5

        for lf_name, lf_curve in config.load_factor_curves.items():
            self.load_factor_curves[lf_name] = lf_curve

        for airline_name, airline_config in config.airlines.items():
            availability_control = self.rm_systems[
                airline_config.rm_system
            ].availability_control
            airline = passengersim.core.Airline(airline_name, availability_control)
            airline.rm_system = self.rm_systems[airline_config.rm_system]
            if airline_config.frat5 is not None and airline_config.frat5 != "":
                f5 = self.frat5curves[airline_config.frat5]
                airline.frat5 = f5
            if (
                airline_config.load_factor_curve is not None
                and airline_config.load_factor_curve != ""
            ):
                lfc = self.load_factor_curves[airline_config.load_factor_curve]
                airline.load_factor_curve = lfc
            self.sim.add_airline(airline)

        self.classes = config.classes
        self.init_rm = {}  # TODO
        self.dcps = config.dcps

        self.curves = {}
        for curve_name, curve_config in config.booking_curves.items():
            bc = passengersim.core.BookingCurve(curve_name)
            bc.random_generator = self.random_generator
            for dcp, pct in curve_config.curve.items():
                bc.add_dcp(dcp, pct)
            self.curves[curve_name] = bc

        self.legs = {}
        for leg_config in config.legs:
            leg = passengersim.core.Leg(
                leg_config.carrier,
                leg_config.fltno,
                leg_config.orig,
                leg_config.dest,
                capacity=leg_config.capacity,
            )
            leg.dep_time = leg_config.dep_time
            leg.arr_time = leg_config.arr_time
            if leg_config.distance:
                leg.distance = leg_config.distance
            elif len(self.airports) > 0:
                leg.distance = self.get_mileage(leg.orig, leg.dest)
            if len(self.classes) > 0:
                self.set_classes(leg)
            self.sim.add_leg(leg)
            if self.debug:
                print(f"Added leg: {leg}, dist = {leg.distance}")
            self.legs[leg.flt_no] = leg

        for dmd_config in config.demands:
            dmd = passengersim.core.Demand(
                dmd_config.orig, dmd_config.dest, dmd_config.segment
            )
            dmd.base_demand = dmd_config.base_demand * self.demand_multiplier
            dmd.price = dmd_config.reference_fare
            dmd.reference_fare = dmd_config.reference_fare
            if len(self.airports) > 0:
                dmd.distance = self.get_mileage(dmd.orig, dmd.dest)
            model_name = dmd_config.choice_model
            cm = self.choice_models.get(model_name, None)
            if cm is not None:
                dmd.add_choice_model(cm)
            if model_name == "business" or dmd_config.segment == "business":
                dmd.business = True
            if dmd_config.curve:
                curve_name = str(dmd_config.curve).strip()
                curve = self.curves[curve_name]
                dmd.add_curve(curve)
            self.sim.add_demand(dmd)
            if self.debug:
                print(f"Added demand: {dmd}, base_demand = {dmd.base_demand}")

        # self.fares = []
        for fare_config in config.fares:
            fare = passengersim.core.Fare(
                fare_config.carrier,
                fare_config.orig,
                fare_config.dest,
                fare_config.booking_class,
                fare_config.price,
            )
            fare.adv_purch = fare_config.advance_purchase
            for rest_code in fare_config.restrictions:
                fare.add_restriction(rest_code)
            self.sim.add_fare(fare)
            if self.debug:
                print(f"Added fare: {fare}")
            # self.fares.append(fare)

        for path_config in config.paths:
            p = passengersim.core.Path(path_config.orig, path_config.dest, 0.0)
            p.path_quality_index = path_config.path_quality_index
            leg_index1 = path_config.legs[0]
            tmp_leg = self.legs[leg_index1]
            assert (
                tmp_leg.orig == path_config.orig
            ), "Path statement is corrupted, orig doesn't match"
            assert tmp_leg.flt_no == leg_index1
            p.add_leg(tmp_leg)
            if len(path_config.legs) >= 2:
                leg_index2 = path_config.legs[1]
                if leg_index2 > 0:
                    tmp_leg = self.legs[leg_index2]
                    p.add_leg(self.legs[leg_index2])
            assert (
                tmp_leg.dest == path_config.dest
            ), "Path statement is corrupted, dest doesn't match"
            self.sim.add_path(p)

        # Go through and make sure things are linked correctly
        for dmd in self.sim.demands:
            for fare in self.sim.fares:
                if fare.orig == dmd.orig and fare.dest == dmd.dest:
                    # print("Joining:", dmd, fare)
                    dmd.add_fare(fare)

        for leg in self.sim.legs:
            for fare in self.sim.fares:
                if (
                    fare.carrier == leg.carrier
                    and fare.orig == leg.orig
                    and fare.dest == leg.dest
                ):
                    leg.set_bucket_decision_fare(fare.booking_class, fare.price)
                    leg.set_bucket_fcst_revenue(fare.booking_class, fare.price)

        self.sim.base_time = config.simulation_controls.reference_epoch()

    def set_classes(self, _leg, debug=False):
        cap = float(_leg.capacity)
        if debug:
            print(_leg, "Capacity = ", cap)
        for bkg_class in self.classes:
            # Input as a percentage
            auth = int(cap * self.init_rm.get(bkg_class, 100.0) / 100.0)
            b = passengersim.core.Bucket(bkg_class, alloc=auth)
            # print("adding bucket", b)
            _leg.add_bucket(b)
            if debug:
                print("    Bucket", bkg_class, auth)

    def setup_scenario(self):
        self.cnx.delete_experiment(self.sim.name)
        logger.debug("building connections")
        num_paths = self.sim.build_connections()
        if num_paths and self.cnx.is_open:
            database.tables.create_table_path_defs(self.cnx._connection, self.sim.paths)
        logger.debug(f"Connections done, num_paths = {num_paths}")
        self.vn_initial_mapping()

    def vn_initial_mapping(self):
        vn_airlines = []
        for airline in self.sim.airlines:
            if airline.control == "vn":
                vn_airlines.append(airline.name)

        for path in self.sim.paths:
            if path.get_leg_carrier(0) in vn_airlines:
                for bc in self.classes:
                    pc = PathClass(bc)
                    index = int(bc[1])
                    pc.set_indexes(index, index)
                    path.add_path_class(pc)

    def _run_sim(self):
        update_freq = self.update_frequency
        logger.debug(
            f"run_sim, num_trials = {self.sim.num_trials}, num_samples = {self.sim.num_samples}"
        )
        self.sim.update_db_write_flags()
        n_samples_total = self.sim.num_trials * self.sim.num_samples
        n_samples_done = 0
        self.sample_done_callback(n_samples_done, n_samples_total)
        if self.sim.config.simulation_controls.show_progress_bar:
            progress = ProgressBar(total=n_samples_total)
        else:
            progress = DummyProgressBar()
        with progress:
            for trial in range(self.sim.num_trials):
                self.sim.trial = trial
                self.sim.reset_trial_counters()
                for sample in range(self.sim.num_samples):
                    if self.sim.config.simulation_controls.double_capacity_until:
                        # Just trying this, PODS has something similar during the burn phase
                        if sample == 0:
                            for leg in self.sim.legs:
                                leg.capacity = leg.capacity * 2.0
                        elif (
                            sample
                            == self.sim.config.simulation_controls.double_capacity_until
                        ):
                            for leg in self.sim.legs:
                                leg.capacity = leg.capacity / 2.0

                    progress.tick(refresh=(sample == 0))
                    self.sim.sample = sample
                    if self.sim.config.simulation_controls.random_seed is not None:
                        self.reseed(
                            [
                                self.sim.config.simulation_controls.random_seed,
                                trial,
                                sample,
                            ]
                        )
                    if update_freq is not None and self.sim.sample % update_freq == 0:
                        total_rev, n = 0.0, 0
                        airline_info = ""
                        for cxr in self.sim.airlines:
                            total_rev += cxr.revenue
                            n += 1
                            airline_info += (
                                f"{', ' if n > 0 else ''}{cxr.name}=${cxr.revenue:8.0f}"
                            )

                        dmd_b, dmd_l = 0, 0
                        for dmd in self.sim.demands:
                            if dmd.business:
                                dmd_b += dmd.scenario_demand
                            else:
                                dmd_l += dmd.scenario_demand
                        d_info = f", {int(dmd_b)}, {int(dmd_l)}"
                        logger.info(
                            f"Trial={self.sim.trial}, Sample={self.sim.sample}{airline_info}{d_info}"
                        )
                    if self.sim.trial > 0 or self.sim.sample > 0:
                        self.sim.reset_counters()
                    self.generate_demands()

                    # Loop on passengers
                    while True:
                        event = self.sim.go()
                        self.run_airline_models(event)
                        if (
                            event is None
                            or str(event) == "Done"
                            or (event[0] == "Done")
                        ):
                            assert (
                                self.sim.num_events() == 0
                            ), f"Event queue still has {self.sim.num_events()} events"
                            break
                    if self.cnx:
                        try:
                            self.cnx.commit()
                        except AttributeError:
                            pass

                    n_samples_done += 1
                    self.sample_done_callback(n_samples_done, n_samples_total)
                if self.cnx.is_open:
                    self.cnx.save_final(self.sim)

    def run_airline_models(self, info: Any = None, departed: bool = False, debug=False):
        event_type = info[0]
        recording_day = info[
            1
        ]  # could in theory also be non-integer for fractional days
        dcp_index = info[2]
        if dcp_index == -1:
            dcp_index = len(self.dcp_list) - 1

        if event_type.lower() in {"dcp", "done"}:
            self.sim.last_dcp = recording_day
            self.capture_dcp_data(dcp_index)

        # This will change once we have "dcp" and "daily" portions of an RM system in the YAML input file
        for airline in self.sim.airlines:
            if event_type.lower() in {"dcp", "done"}:
                airline.rm_system.run(self.sim, airline.name, dcp_index, recording_day)
            elif event_type.lower() == "daily":
                pass

        if event_type.lower() in {"dcp", "done"}:
            if self.cnx.is_open:
                self.cnx.save_details(self.sim, recording_day)
            if self.file_writer is not None:
                self.file_writer.save_details(self.sim, recording_day)

    def capture_dcp_data(self, dcp_index):
        for leg in self.sim.legs:
            leg.capture_dcp(dcp_index)
        for path in self.sim.paths:
            path.capture_dcp(dcp_index)

    def _accum_by_tf(self, dcp_index):
        # This is now replaced by C++ native counters ...
        if dcp_index > 0:
            prev_dcp = self.dcp_list[dcp_index - 1]
            for f in self.sim.fares:
                curr_business = self.fare_sales_by_dcp.get(("business", prev_dcp), 0)
                curr_leisure = self.fare_sales_by_dcp.get(("leisure", prev_dcp), 0)
                inc_leisure = curr_leisure + (f.sold - f.sold_business)
                inc_business = curr_business + f.sold_business
                self.fare_sales_by_dcp[("business", prev_dcp)] = inc_business
                self.fare_sales_by_dcp[("leisure", prev_dcp)] = inc_leisure

                key2 = (f.carrier, prev_dcp)
                curr_airline = self.fare_sales_by_airline_dcp[key2]
                self.fare_sales_by_airline_dcp[key2] = curr_airline + f.sold

                key3 = (f.carrier, f.booking_class, prev_dcp)
                self.fare_details_sold[key3] += f.sold
                self.fare_details_sold_business[key3] += f.sold_business
                self.fare_details_revenue[key3] += f.price * f.sold

    def generate_dcp_rm_events(self, debug=False):
        """Pushes an event per reading day (DCP) onto the queue.
        Also adds events for daily reoptimzation"""
        dcp_hour = self.sim.config.simulation_controls.dcp_hour
        if debug:
            tmp = datetime.fromtimestamp(self.sim.base_time, tz=timezone.utc)
            print(f"Base Time is {tmp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        for dcp_index, dcp in enumerate(self.dcp_list):
            if dcp == 0:
                continue
            event_time = int(self.sim.base_time - dcp * 86400 + 3600 * dcp_hour)
            if debug:
                tmp = datetime.fromtimestamp(event_time, tz=timezone.utc)
                print(f"Added DCP {dcp} at {tmp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            info = ("DCP", dcp, dcp_index)
            rm_event = Event(info, event_time)
            self.sim.add_event(rm_event)

        # Now add the events for daily reoptimization
        max_days_prior = max(self.dcp_list)
        for days_prior in range(max_days_prior):
            if days_prior not in self.dcp_list:
                info = ("daily", days_prior, 0)
                event_time = int(
                    self.sim.base_time - days_prior * 86400 + 3600 * dcp_hour
                )
                rm_event = Event(info, event_time)
                self.sim.add_event(rm_event)

    def generate_demands(self, system_rn=None, debug=False):
        """Generate demands, following the procedure used in PODS
        The biggest difference is that we can put all the timeframe (DCP) demands
        into the event queue before any processing.
        For large models, I might rewrite this into the C++ core in the future"""
        self.generate_dcp_rm_events()
        total_events = 0
        system_rn = (
            self.random_generator.get_normal() if system_rn is None else system_rn
        )

        # We don't have an O&D object, but we use this to get a market random number per market
        mrn_ref = {}

        # Need to have leisure / business split for PODS
        trn_ref = {
            "business": self.random_generator.get_normal(),
            "leisure": self.random_generator.get_normal(),
        }

        def get_or_make_random(grouping, key):
            if key not in grouping:
                grouping[key] = self.random_generator.get_normal()
            return grouping[key]

        end_time = self.base_time

        for dmd in self.sim.demands:
            base = dmd.base_demand

            # Get the random numbers we're going to use to perturb demand
            trn = get_or_make_random(trn_ref, (dmd.orig, dmd.dest, dmd.segment))
            mrn = get_or_make_random(mrn_ref, (dmd.orig, dmd.dest))
            if self.sim.config.simulation_controls.simple_k_factor:
                urn = (
                    self.random_generator.get_normal()
                    * self.sim.config.simulation_controls.simple_k_factor
                )
            else:
                urn = 0

            mu = base * (
                1.0
                + system_rn * self.sim.sys_k_factor
                + mrn * self.sim.mkt_k_factor
                + trn * self.sim.pax_type_k_factor
                + urn
            )
            mu = max(mu, 0.0)
            sigma = sqrt(
                mu * self.sim.config.simulation_controls.tot_z_factor
            )  # Correct?
            n = mu + sigma * self.random_generator.get_normal()
            dmd.scenario_demand = max(n, 0)

            if debug:
                logger.debug(
                    f"DMD,{self.sim.sample},{dmd.orig},{dmd.dest},{dmd.segment},{dmd.base_demand},"
                    f"{round(mu,2)},{round(sigma,2)},{round(n,2)}"
                )

            # Now we split it up over timeframes and add it to the simulation
            num_pax = int(dmd.scenario_demand + 0.5)  # rounding
            if (
                self.sim.config.simulation_controls.timeframe_demand_allocation
                == "pods"
            ):
                num_events_by_tf = self.sim.allocate_demand_to_tf_pods(
                    dmd, num_pax, self.sim.tf_k_factor, int(end_time)
                )
            else:
                num_events_by_tf = self.sim.allocate_demand_to_tf(
                    dmd, num_pax, self.sim.tf_k_factor, int(end_time)
                )
            num_events = sum(num_events_by_tf)
            total_events += num_events
            if num_events != round(num_pax):
                # print(f"Generate demand function, num_pax={num_pax}, num_events={num_events}")
                raise Exception(
                    f"Generate demand function, num_pax={num_pax}, num_events={num_events}"
                )

        return total_events

    # def data_by_timeframe(self):
    #     logger.info("----- Demand By DCP -----")
    #     dmd_by_tf = defaultdict(float)
    #     for dmd in self.sim.demands:
    #         for dcp in self.dcp_list:
    #             if dcp == 0:
    #                 continue
    #             dmd_by_tf[(dmd.curve_number, dcp)] += dmd.get_demand_dcp(dcp)
    #     for k, v in dmd_by_tf.items():
    #         logger.info(f"    {k[0]}, {k[1]}, {v}")
    #
    #     total_samples = self.sim.num_trials * self.sim.num_samples
    #     logger.info(
    #         f"Fare Sales by DCP (dcp, business, tf_business, leisure, tf_leisure), samples = {total_samples}"
    #     )
    #     prev_b, prev_l = 0, 0
    #     for dcp in self.dcp_list:
    #         if dcp == 0:
    #             continue
    #         business = self.fare_sales_by_dcp[("business", dcp)]
    #         leisure = self.fare_sales_by_dcp[("leisure", dcp)]
    #         logger.info(
    #             f"    {dcp}, {business}, {business - prev_b}, {leisure}, {leisure - prev_l}"
    #         )
    #         prev_b, prev_l = business, leisure
    #
    #     logger.info("Fare Sales by DCP & airline (dcp, Al1, AL2, ...etc)")
    #     prev = defaultdict(int)
    #     for dcp in self.dcp_list:
    #         if dcp == 0:
    #             continue
    #         tmp = ""
    #         for a in self.sim.airlines:
    #             sold = self.fare_sales_by_airline_dcp[(a.name, dcp)]
    #             inc_sold = sold - prev[a.name]
    #             tmp += str(inc_sold) if tmp == "" else (", " + str(inc_sold))
    #             prev[a.name] = sold
    #         logger.info(f"    {dcp}, {tmp}")
    #
    #     logger.info(
    #         "Fare Details:  Airline, Class, RRD, Sold, Business, Leisure, AvgPrice"
    #     )
    #     my_keys = self.fare_details_sold.keys()
    #     my_keys = sorted(my_keys, key=lambda x: (x[0], x[1], 100 - x[2]))
    #     prev_dcp, prev_sold, prev_business, prev_leisure = 0, 0, 0, 0
    #     for k in my_keys:
    #         dcp = k[2]
    #         if int(dcp) > int(prev_dcp):
    #             prev_sold, prev_business, prev_leisure = 0, 0, 0
    #         sold = self.fare_details_sold[k]
    #         sold_business = self.fare_details_sold_business[k]
    #         sold_leisure = sold - sold_business
    #         avg_price = self.fare_details_revenue[k] / sold if sold > 0 else 0.0
    #         logger.info(
    #             f"    {k[0]:4} {k[1]:4} {k[2]:4} "
    #             f"{sold - prev_sold:8} {sold_business - prev_business:8} "
    #             f"{sold_leisure - prev_leisure:8} {avg_price:10.2f}"
    #         )
    #         prev_dcp, prev_sold, prev_business, prev_leisure = (
    #             dcp,
    #             sold,
    #             sold_business,
    #             sold_leisure,
    #         )

    def compute_reports(
        self,
        sim: SimulationEngine,
        to_log=True,
        to_db: bool | database.Database = True,
        additional=(
            "fare_class_mix",
            "load_factors",
            "bookings_by_timeframe",
            "total_demand",
        ),
    ) -> SummaryTables:
        num_samples = sim.num_trials * (sim.num_samples - sim.burn_samples)
        if num_samples <= 0:
            raise ValueError(
                "insufficient number of samples outside burn period for reporting"
                f"\n- num_trials = {sim.num_trials}"
                f"\n- num_samples = {sim.num_samples}"
                f"\n- burn_samples = {sim.burn_samples}"
            )

        if to_db is True:
            to_db = self.cnx
        dmd_df = self.compute_demand_report(sim, to_log, to_db)
        fare_df = self.compute_fare_report(sim, to_log, to_db)
        leg_df = self.compute_leg_report(sim, to_log, to_db)
        path_df = self.compute_path_report(sim, to_log, to_db)
        path_classes_df = self.compute_path_class_report(sim, to_log, to_db)
        carrier_df = self.compute_carrier_report(sim, to_log, to_db)

        summary = SummaryTables(
            demands=dmd_df,
            fares=fare_df,
            legs=leg_df,
            paths=path_df,
            path_classes=path_classes_df,
            carriers=carrier_df,
        )
        summary.load_additional_tables(self.cnx, sim.name, sim.burn_samples, additional)
        return summary

    def compute_demand_report(
        self, sim: SimulationEngine, to_log=True, to_db: database.Database | None = None
    ):
        dmd_df = []
        for m in sim.demands:
            avg_price = m.revenue / m.sold if m.sold > 0 else 0
            dmd_df.append(
                dict(
                    orig=m.orig,
                    dest=m.dest,
                    segment=m.segment,
                    sold=m.sold,
                    revenue=m.revenue,
                    avg_fare=m.revenue / m.sold if m.sold > 0 else 0,
                    gt_demand=m.gt_demand,
                    gt_sold=m.gt_sold,
                    gt_revenue=m.gt_revenue,
                )
            )
            if to_log:
                logger.info(
                    f"   Dmd: {m.orig}-{m.dest}:{m.segment}"
                    f"  Sold = {m.sold},  "
                    f"Rev = {m.revenue}, "
                    f"AvgFare = {avg_price:.2f}"
                )
        dmd_df = pd.DataFrame(dmd_df)
        if to_db and to_db.is_open:
            to_db.save_dataframe("demand_summary", dmd_df)
        return dmd_df

    def compute_fare_report(
        self, sim: SimulationEngine, to_log=True, to_db: database.Database | None = None
    ):
        fare_df = []
        for f in sim.fares:
            for dcp_index in range(16):
                fare_df.append(
                    dict(
                        carrier=f.carrier,
                        orig=f.orig,
                        dest=f.dest,
                        booking_class=f.booking_class,
                        dcp_index=dcp_index,
                        price=f.price,
                        sold=f.sold,
                        gt_sold=f.gt_sold,
                        avg_adjusted_price=f.get_adjusted_by_dcp(dcp_index),
                    )
                )
                if to_log:
                    logger.info(
                        f"   Fare: {f.carrier} {f.orig}-{f.dest}:{f.booking_class}"
                        # f"AvgAdjFare = {avg_adj_price:.2f},"
                        f"  Sold = {f.sold},  "
                        f"Price = {f.price}"
                    )
        fare_df = pd.DataFrame(fare_df)
        #        if to_db and to_db.is_open:
        #            to_db.save_dataframe("fare_summary", fare_df)
        return fare_df

    def compute_leg_report(
        self, sim: SimulationEngine, to_log=True, to_db: database.Database | None = None
    ):
        num_samples = sim.num_trials * (sim.num_samples - sim.burn_samples)
        leg_df = []
        for leg in sim.legs:
            avg_sold = leg.gt_sold / num_samples
            avg_rev = leg.gt_revenue / num_samples
            lf = 100.0 * leg.gt_sold / (leg.capacity * num_samples)
            if to_log:
                logger.info(
                    f"    Leg: {leg.carrier}:{leg.flt_no} {leg.orig}-{leg.dest}: "
                    f" AvgSold = {avg_sold:6.2f},  AvgRev = ${avg_rev:,.2f}, LF = {lf:,.2f}%"
                )
            leg_df.append(
                dict(
                    carrier=leg.carrier,
                    flt_no=leg.flt_no,
                    orig=leg.orig,
                    dest=leg.dest,
                    avg_sold=avg_sold,
                    avg_rev=avg_rev,
                    lf=lf,
                )
            )
        leg_df = pd.DataFrame(leg_df)
        if to_db and to_db.is_open:
            to_db.save_dataframe("leg_summary", leg_df)
        return leg_df

    def compute_path_report(
        self, sim: SimulationEngine, to_log=True, to_db: database.Database | None = None
    ):
        num_samples = sim.num_trials * (sim.num_samples - sim.burn_samples)
        avg_lf, n = 0.0, 0
        for leg in sim.legs:
            lf = 100.0 * leg.gt_sold / (leg.capacity * num_samples)
            avg_lf += lf
            n += 1

        tot_rev = 0.0
        for m in sim.demands:
            tot_rev += m.revenue

        avg_lf = avg_lf / n if n > 0 else 0
        if to_log:
            logger.info(f"    LF:  {avg_lf:6.2f}%, Total revenue = ${tot_rev:,.2f}")

        path_df = []
        for path in sim.paths:
            avg_sold = path.gt_sold / num_samples
            avg_sold_priceable = path.gt_sold_priceable / num_samples
            avg_rev = path.gt_revenue / num_samples
            if to_log:
                logger.info(
                    f"{path}, avg_sold={avg_sold:6.2f}, avg_rev=${avg_rev:10,.2f}"
                )
            if path.num_legs() == 1:
                path_df.append(
                    dict(
                        orig=path.orig,
                        dest=path.dest,
                        carrier1=path.get_leg_carrier(0),
                        flt_no1=path.get_leg_fltno(0),
                        carrier2=None,
                        flt_no2=None,
                        avg_sold=avg_sold,
                        avg_sold_priceable=avg_sold_priceable,
                        avg_rev=avg_rev,
                    )
                )
            elif path.num_legs() == 2:
                path_df.append(
                    dict(
                        orig=path.orig,
                        dest=path.dest,
                        carrier1=path.get_leg_carrier(0),
                        flt_no1=path.get_leg_fltno(0),
                        carrier2=path.get_leg_carrier(1),
                        flt_no2=path.get_leg_fltno(1),
                        avg_sold=avg_sold,
                        avg_sold_priceable=avg_sold_priceable,
                        avg_rev=avg_rev,
                    )
                )
            else:
                raise NotImplementedError("path with other than 1 or 2 legs")
        path_df = pd.DataFrame(path_df)
        if to_db and to_db.is_open:
            to_db.save_dataframe("path_summary", path_df)
        return path_df

    def compute_path_class_report(
        self, sim: SimulationEngine, to_log=True, to_db: database.Database | None = None
    ):
        num_samples = sim.num_trials * (sim.num_samples - sim.burn_samples)
        # avg_lf, n = 0.0, 0
        #        for leg in sim.legs:
        #            lf = 100.0 * leg.gt_sold / (leg.capacity * num_samples)
        #            avg_lf += lf
        #            n += 1

        #        tot_rev = 0.0
        #        for m in sim.demands:
        #            tot_rev += m.revenue

        #        avg_lf = avg_lf / n if n > 0 else 0
        #        if to_log:
        #            logger.info(f"    LF:  {avg_lf:6.2f}%, Total revenue = ${tot_rev:,.2f}")

        path_class_df = []
        for path in sim.paths:
            for pc in path.pathclasses:
                avg_sold = pc.gt_sold / num_samples
                avg_sold_priceable = pc.gt_sold_priceable / num_samples
                avg_rev = pc.gt_revenue / num_samples
                if to_log:
                    logger.info(
                        f"{pc}, avg_sold={avg_sold:6.2f}, avg_rev=${avg_rev:10,.2f}"
                    )
                if path.num_legs() == 1:
                    path_class_df.append(
                        dict(
                            orig=path.orig,
                            dest=path.dest,
                            carrier1=path.get_leg_carrier(0),
                            flt_no1=path.get_leg_fltno(0),
                            carrier2=None,
                            flt_no2=None,
                            booking_class=pc.booking_class,
                            avg_sold=avg_sold,
                            avg_sold_priceable=avg_sold_priceable,
                            avg_rev=avg_rev,
                        )
                    )
                elif path.num_legs() == 2:
                    path_class_df.append(
                        dict(
                            orig=path.orig,
                            dest=path.dest,
                            carrier1=path.get_leg_carrier(0),
                            flt_no1=path.get_leg_fltno(0),
                            carrier2=path.get_leg_carrier(1),
                            flt_no2=path.get_leg_fltno(1),
                            booking_class=pc.booking_class,
                            avg_sold=avg_sold,
                            avg_sold_priceable=avg_sold_priceable,
                            avg_rev=avg_rev,
                        )
                    )
                else:
                    raise NotImplementedError("path with other than 1 or 2 legs")
        path_class_df = pd.DataFrame(path_class_df)
        path_class_df.sort_values(
            by=["orig", "dest", "carrier1", "flt_no1", "booking_class"]
        )
        #        if to_db and to_db.is_open:
        #            to_db.save_dataframe("path_class_summary", path_class_df)
        return path_class_df

    def compute_carrier_report(
        self,
        sim: SimulationEngine,
        to_log: bool = True,
        to_db: database.Database | None = None,
    ) -> pd.DataFrame:
        """
        Compute a carrier summary table.

        The resulting table has one row per simulated carrier, and the following
        columns:

        - name
        - avg_sold
        - load_factor
        - avg_rev
        - asm (available seat miles)
        - rpm (revenue passenger miles)
        """
        num_samples = sim.num_trials * (sim.num_samples - sim.burn_samples)
        carrier_df = []

        airline_asm = defaultdict(float)
        airline_rpm = defaultdict(float)
        airline_leg_lf = defaultdict(float)
        airline_leg_count = defaultdict(float)
        for leg in sim.legs:
            airline_asm[leg.carrier] += leg.distance * leg.capacity * num_samples
            airline_rpm[leg.carrier] += leg.distance * leg.gt_sold
            airline_leg_lf[leg.carrier] += leg.gt_sold / (leg.capacity * num_samples)
            airline_leg_count[leg.carrier] += 1

        for cxr in sim.airlines:
            avg_sold = cxr.gt_sold / num_samples
            avg_rev = cxr.gt_revenue / num_samples
            asm = airline_asm[cxr.name] / num_samples
            rpm = airline_rpm[cxr.name] / num_samples
            # sys_lf = 100.0 * cxr.gt_revenue_passenger_miles / asm if asm > 0 else 0.0
            denom = airline_asm[cxr.name]
            sys_lf = (100.0 * airline_rpm[cxr.name] / denom) if denom > 0 else 0
            if to_log:
                logger.info(
                    f"Airline: {cxr.name}, AvgSold: {round(avg_sold, 2)}, LF {sys_lf:.2f}%,  AvgRev ${avg_rev:10,.2f}"
                )
            carrier_df.append(
                {
                    "carrier": cxr.name,
                    "sold": round(avg_sold, 2),
                    "sys_lf": round(sys_lf, 3),
                    "avg_leg_lf": round(
                        100 * airline_leg_lf[cxr.name] / airline_leg_count[cxr.name], 3
                    ),
                    "avg_rev": (round(avg_rev, 0)),
                    "avg_price": round(avg_rev / avg_sold, 2),
                    "asm": (round(asm, 0)),
                    "rpm": (round(rpm, 0)),
                    "yield": np.nan if rpm == 0 else round(avg_rev / rpm, 4),
                }
            )
            # logger.info(f"ASM = {airline_asm[cxr.name]:.2f}, RPM = {airline_rpm[cxr.name]:.2f}, LF = {sys_lf:.2f}%")
        carrier_df = pd.DataFrame(carrier_df)
        if to_db and to_db.is_open:
            to_db.save_dataframe("carrier_summary", carrier_df)
        return carrier_df

    def reseed(self, seed: int | list[int] | None = 42):
        logger.debug("reseeding random_generator: %s", seed)
        self.sim.random_generator.seed(seed)

    def _user_certificate(self, certificate_filename=None):
        if certificate_filename:
            from cryptography.x509 import load_pem_x509_certificate

            certificate_filename = pathlib.Path(certificate_filename)
            with certificate_filename.open("rb") as f:
                user_cert = load_pem_x509_certificate(f.read())
        else:
            user_cert = self.sim.config.license_certificate
        return user_cert

    def validate_license(self, certificate_filename=None, future: int = 0):
        user_cert = self._user_certificate(certificate_filename)
        return self.sim.validate_license(user_cert, future=future)

    def license_info(self, certificate_filename=None):
        user_cert = self._user_certificate(certificate_filename)
        return self.sim.license_info(user_cert)

    @property
    def config(self) -> Config:
        """The configuration used for this Simulation."""
        return self.sim.config

    def run(self, log_reports: bool = False) -> SummaryTables:
        start_time = time.time()
        self.setup_scenario()
        self._run_sim()
        summary = self.compute_reports(
            self.sim,
            to_log=log_reports or self.sim.config.outputs.log_reports,
            additional=self.sim.config.outputs.reports,
        )
        if self.sim.config.outputs.excel:
            summary.to_xlsx(self.sim.config.outputs.excel)
        logger.info(
            f"Th' th' that's all folks !!!    (Elapsed time = {round(time.time() - start_time, 2)})"
        )
        return summary

    def backup_db(self, dst: pathlib.Path | str | sqlite3.Connection):
        """Back up this database to another copy.

        Parameters
        ----------
        dst : Path-like or sqlite3.Connection
        """
        return self.cnx.backup(dst)

    def path_names(self):
        result = {}
        for p in self.sim.paths:
            result[p.path_id] = str(p)
        return result
