import gzip
import logging
import os
import pathlib
import time
from collections import defaultdict
from datetime import datetime
from math import sqrt
from typing import Any

import AirSim
import yaml
from AirSim import PathClass
from AirSim.utils import FileWriter, airsim_utils, db_utils
from numpy import random

from .config import AirSimConfig

logger = logging.getLogger("AirSim")


class Simulation:
    @classmethod
    def from_yaml(
        cls,
        filenames: pathlib.Path | list[pathlib.Path],
        output_dir: pathlib.Path | None = None,
    ):
        if isinstance(filenames, str | pathlib.Path):
            filenames = [filenames]
        raw_config = {}
        for filename in reversed(filenames):
            filename = pathlib.Path(filename)
            opener = gzip.open if filename.suffix == ".gz" else open
            with opener(filename) as f:
                content = yaml.safe_load(f)
                raw_config.update(content)
        config = AirSimConfig.model_validate(raw_config)
        return cls(config, output_dir)

    def __init__(
        self,
        config: AirSimConfig,
        output_dir: pathlib.Path | None = None,
    ):
        if output_dir is None:
            import tempfile

            self._tempdir = tempfile.TemporaryDirectory()
            output_dir = os.path.join(self._tempdir.name, "test1")
        self.sim = AirSim.AirSim("None")
        self.cnx = None
        if config.simulation_controls.write_raw_files:
            self.file_writer = FileWriter.FileWriter(output_dir)
        else:
            self.file_writer = None
        self.base_date = datetime.fromisoformat("2020-01-01 00:00:00")
        #        self.dcp_list = [63, 24, 17, 10, 5]
        self.dcp_list = [63, 56, 49, 42, 35, 31, 28, 24, 21, 17, 14, 10, 7, 5, 3, 1, 0]
        self.classes = []
        self.fare_sales_by_dcp = defaultdict(int)
        self.fare_sales_by_airline_dcp = defaultdict(int)
        self.fare_details_sold = defaultdict(int)
        self.fare_details_sold_business = defaultdict(int)
        self.fare_details_revenue = defaultdict(float)
        self.db_engine = config.db.engine
        self.db_filename = config.db.filename
        self.output_dir = output_dir
        self.snapshot_filters = []

    def setup_scenario(self):
        if self.cnx is not None:
            db_utils.delete_experiment(self.cnx, self.sim.name)
        logger.info("building connections")
        num_paths = self.sim.build_connections()
        logger.info(f"Connections done, num_paths = {num_paths}")
        self.vn_initial_mapping()

    def vn_initial_mapping(self):
        vn_airlines = []
        for airline in self.sim.airlines:
            if airline.use_vn:
                vn_airlines.append(airline.name)

        for path in self.sim.paths:
            if path.get_leg_carrier(0) in vn_airlines:
                for bc in self.classes:
                    pc = PathClass(bc)
                    index = int(bc[1])
                    pc.set_indexes(index, index)
                    path.add_path_class(pc)

    def run_sim(self):
        logger.info(
            f"run_sim, num_trials = {self.sim.num_trials}, num_samples = {self.sim.num_samples}"
        )
        for trial in range(self.sim.num_trials):
            self.sim.trial = trial
            for sample in range(self.sim.num_samples):
                self.sim.sample = sample
                if self.sim.sample % 1 == 0:
                    avg_rev, n = 0.0, 0
                    airline_info = ""
                    for cxr in self.sim.airlines:
                        avg_rev += cxr.revenue
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
                    avg_rev = avg_rev / n
                    # logger.info(
                    # f"********** Trial = {self.sim.trial}, Sample = {self.sim.sample}, AvgRev = ${avg_rev:11,.2f}"
                    # )
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
                    if event is None or str(event) == "Done":
                        assert (
                            self.sim.num_events() == 0
                        ), f"Event queue still has {self.sim.num_events()} events"
                        break

    def run_airline_models(self, info: Any = None, departed: bool = False, debug=False):
        dcp = 0 if info == "Done" else info[1]
        dcp_index = len(self.dcp_list) - 1 if info == "Done" else info[2]
        self.sim.last_dcp = dcp
        for leg in self.sim.legs:
            # Just trying this, PODS has something similar during the burn phase
            # if sample == 1:
            #    leg.capacity = leg.capacity * 2.0
            # elif sample == 80:
            #    leg.capacity = leg.capacity / 2.0

            leg.capture_dcp(dcp_index)
            if self.sim.sample == 2000 and leg.flt_no == 101:
                logger.info(f"---------- DCP = {dcp} ----------")
                leg.print_bucket_detail()

        for path in self.sim.paths:
            path.capture_dcp(dcp_index)

        for airline in self.sim.airlines:
            # logger.info(f"Running RM for {airline}, dcp={dcp}")
            airline.rm_system.run(self.sim, airline.name, dcp_index, dcp)

        #        # logger.info(f"************************** DCP = {dcp} **************************")
        if self.cnx is not None:
            db_utils.save_details(self.cnx, self.sim, dcp)
        if self.file_writer is not None:
            self.file_writer.save_details(self.sim, dcp)

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

                # if f.carrier == "AL1" and f.orig == "BOS" and f.dest == "ORD" and f.booking_class == "Y1":
                #    print(f"    {f.carrier}:{f.orig}-{f.dest}, {f.booking_class},
                #    tmp_dcp={prev_dcp}, dcp_index={dcp_index}, {f.sold}, {f.sold_business}")

    def generate_demands(self, system_rn=None, debug=False):
        """Generate demands, following the procedure used in PODS
        The biggest difference is that we can put all the timeframe (DCP) demands
        into the event queue before any processing.
        For large models, I might rewrite this into the C++ core in the future"""
        airsim_utils.add_dcp(self.sim, self.base_date, 0, self.dcp_list, debug=False)
        total_events = 0
        system_rn = random.normal() if system_rn is None else system_rn

        # We don't have an O&D object, but we use this to get a market random number per market
        mrn_ref = {}

        # Need to have leisure / business split for PODS
        {"business": random.normal(), "leisure": random.normal()}

        end_time = (self.base_date - datetime(1970, 1, 1)).total_seconds()

        for dmd in self.sim.demands:
            base = dmd.base_demand

            # Get the random numbers we're going to use to perturb demand
            # trn = trn_ref.get(dmd.segment, 0.0)
            trn = random.normal()
            key = (dmd.orig, dmd.dest)
            if key in mrn_ref:
                mrn = mrn_ref[key]
            else:
                mrn = random.normal()
                mrn_ref[key] = mrn

            mu = base * (
                1.0
                + system_rn * self.sim.sys_k_factor
                + mrn * self.sim.mkt_k_factor
                + trn * self.sim.pax_type_k_factor
            )
            sigma = sqrt(abs(mu) * self.sim.z_factor)
            n = mu + sigma * random.normal()
            dmd.scenario_demand = max(n, 0)

            if debug:
                logger.debug(
                    f"DMD,{self.sim.sample},{dmd.orig},{dmd.dest},{dmd.segment},{dmd.base_demand},"
                    f"{round(mu,2)},{round(sigma,2)},{round(n,2)}"
                )

            # Now we split it up over timeframes and add it to the simulation
            num_pax = int(dmd.scenario_demand)
            num_events = self.sim.allocate_demand_to_tf(
                dmd, num_pax, self.sim.tf_k_factor, int(end_time)
            )
            total_events += num_events
            if num_events != round(num_pax):
                # print(f"Generate demand function, num_pax={num_pax}, num_events={num_events}")
                raise Exception(
                    f"Generate demand function, num_pax={num_pax}, num_events={num_events}"
                )

        return total_events

    def run_reports(self, sim: AirSim.AirSim):
        num_samples = sim.num_trials * (sim.num_samples - sim.burn_samples)
        if num_samples <= 0:
            raise ValueError(
                "insufficient number of samples outside burn period for reporting"
                f"\n- num_trials = {sim.num_trials}"
                f"\n- num_samples = {sim.num_samples}"
                f"\n- burn_samples = {sim.burn_samples}"
            )
        tot_rev = 0.0
        for m in sim.demands:
            avg_price = m.revenue / m.sold if m.sold > 0 else 0
            logger.info(
                f"   Dmd: {m.orig}-{m.dest}:{m.segment}"
                f"  Sold = {m.sold},  "
                f"Rev = {m.revenue}, "
                f"AvgFare = {avg_price:.2f}"
            )
            tot_rev += m.revenue

        avg_lf, n = 0, 0, 0.0, 0
        airline_asm = defaultdict(float)
        airline_rpm = defaultdict(float)
        for leg in sim.legs:
            avg_sold = leg.gt_sold / num_samples
            avg_rev = leg.gt_revenue / num_samples
            lf = 100.0 * leg.gt_sold / (leg.capacity * num_samples)
            logger.info(
                f"    Leg: {leg.carrier}:{leg.flt_no} {leg.orig}-{leg.dest}: "
                f" AvgSold = {avg_sold:6.2f},  AvgRev = ${avg_rev:,.2f}, LF = {lf:,.2f}%"
            )
            avg_lf += lf
            n += 1
            airline_asm[leg.carrier] += leg.distance * leg.capacity * num_samples
            airline_rpm[leg.carrier] += leg.distance * leg.gt_sold

        avg_lf = avg_lf / n if n > 0 else 0
        logger.info(f"    LF:  {avg_lf:6.2f}%, Total revenue = ${tot_rev:,.2f}")

        for path in sim.paths:
            avg_sold = path.gt_sold / num_samples
            avg_rev = path.gt_revenue / num_samples
            logger.info(f"{path}, avg_sold={avg_sold:6.2f}, avg_rev=${avg_rev:10,.2f}")

        for cxr in sim.airlines:
            avg_sold = round(cxr.gt_sold / num_samples)
            avg_rev = cxr.gt_revenue / num_samples
            # asm = cxr.gt_available_seat_miles
            # lf2 = 100.0 * cxr.gt_revenue_passenger_miles / asm if asm > 0 else 0.0
            denom = airline_asm[cxr.name]
            lf2 = (100.0 * airline_rpm[cxr.name] / denom) if denom > 0 else 0
            logger.info(
                f"Airline: {cxr.name}, AvgSold: {avg_sold}, LF {lf2:.2f}%,  AvgRev ${avg_rev:10,.2f}"
            )
            # logger.info(f"ASM = {airline_asm[cxr.name]:.2f}, RPM = {airline_rpm[cxr.name]:.2f}, LF = {lf2:.2f}%") #***

    def run(self):
        start_time = time.time()
        self.setup_scenario()
        self.run_sim()
        self.run_reports(self.sim)
        logger.info(
            f"Th' th' that's all folks !!!    (Elapsed time = {round(time.time() - start_time, 2)})"
        )
