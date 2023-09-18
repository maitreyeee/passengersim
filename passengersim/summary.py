import logging
import os.path
import pathlib
from collections.abc import Collection
from typing import Literal

import numpy as np
import pandas as pd

from . import database
from .reporting import report_figure

logger = logging.getLogger("passengersim.summary")


class SummaryTables:
    @classmethod
    def from_sqlite(
        cls,
        filename: str,
        make_indexes: bool = False,
        additional: Collection[str | tuple] = (
            "fare_class_mix",
            "load_factors",
            "bookings_by_timeframe",
            "total_demand",
        ),
    ):
        if not os.path.isfile(filename):
            raise FileNotFoundError(filename)
        db = database.Database(
            engine="sqlite",
            filename=filename,
        )

        demands = cls.load_basic_table(db, "demand_summary")
        legs = cls.load_basic_table(db, "leg_summary")
        paths = cls.load_basic_table(db, "path_summary")
        carriers = cls.load_basic_table(db, "carrier_summary")

        summary = cls(
            demands=demands,
            legs=legs,
            paths=paths,
            carriers=carriers,
        )

        if make_indexes:
            db.add_indexes()

        logger.info("loading configs")
        config = db.load_configs()

        summary.load_additional_tables(
            db,
            scenario=config.scenario,
            burn_samples=config.simulation_controls.burn_samples,
            additional=additional,
        )
        summary.cnx = db
        return summary

    @classmethod
    def load_basic_table(self, db: database.Database, tablename: str):
        """Load a basic table"""
        logger.info("loading %s", tablename)
        return db.dataframe(f"SELECT * FROM {tablename}")

    def load_additional_tables(
        self,
        db: database.Database,
        scenario: str,
        burn_samples: int,
        additional: Collection[str | tuple] = (
            "fare_class_mix",
            "load_factors",
            "bookings_by_timeframe",
            "total_demand",
        ),
    ) -> None:
        if "fare_class_mix" in additional and db.is_open:
            logger.info("loading fare_class_mix")
            self.fare_class_mix = database.common_queries.fare_class_mix(
                db, scenario, burn_samples=burn_samples
            )
            if self.od_fare_class_mix:
                for orig, dest in list(self.od_fare_class_mix):
                    self.od_fare_class_mix[
                        (orig, dest)
                    ] = database.common_queries.od_fare_class_mix(
                        db, orig, dest, scenario, burn_samples=burn_samples
                    )

        for i in additional:
            if isinstance(i, tuple) and i[0] == "od_fare_class_mix" and db.is_open:
                orig, dest = i[1], i[2]
                if self.od_fare_class_mix is None:
                    self.od_fare_class_mix = {}
                logger.info(f"loading od_fare_class_mix({orig},{dest})")
                self.od_fare_class_mix[
                    (orig, dest)
                ] = database.common_queries.od_fare_class_mix(
                    db, orig, dest, scenario, burn_samples=burn_samples
                )

        if "load_factors" in additional and db.is_open:
            logger.info("loading load_factors")
            self.load_factors = database.common_queries.load_factors(
                db, scenario, burn_samples=burn_samples
            )

        if "bookings_by_timeframe" in additional and db.is_open:
            logger.info("loading bookings_by_timeframe")
            self.bookings_by_timeframe = database.common_queries.bookings_by_timeframe(
                db, scenario, burn_samples=burn_samples
            )

        if "total_demand" in additional and db.is_open:
            logger.info("loading total_demand")
            self.total_demand = database.common_queries.total_demand(
                db, scenario, burn_samples
            )

    def __init__(
        self,
        demands: pd.DataFrame | None = None,
        legs: pd.DataFrame | None = None,
        paths: pd.DataFrame | None = None,
        carriers: pd.DataFrame | None = None,
        fare_class_mix: pd.DataFrame | None = None,
        load_factors: pd.DataFrame | None = None,
        bookings_by_timeframe: pd.DataFrame | None = None,
        total_demand: float | None = None,
        od_fare_class_mix: dict[tuple[str, str], pd.DataFrame] | None = None,
    ):
        self.demands = demands
        self.legs = legs
        self.paths = paths
        self.carriers = carriers
        self.fare_class_mix = fare_class_mix
        self.od_fare_class_mix = od_fare_class_mix
        self.load_factors = load_factors
        self.bookings_by_timeframe = bookings_by_timeframe
        self.total_demand = total_demand

    def to_records(self):
        return {k: v.to_dict(orient="records") for (k, v) in self.__dict__.items()}

    def to_xlsx(self, filename: str | pathlib.Path) -> None:
        """Write summary tables to excel.

        Parameters
        ----------
        filename : Pathlike
            The excel file to write.
        """
        if isinstance(filename, str):
            filename = pathlib.Path(filename)
        filename.parent.mkdir(exist_ok=True, parents=True)
        with pd.ExcelWriter(filename) as writer:
            for k, v in self.__dict__.items():
                if isinstance(v, pd.DataFrame):
                    v.to_excel(writer, sheet_name=k)

    def fig_carrier_loads(self, raw_df=False, report=None):
        """Figure showing ASM, RPM by carrier."""
        df = (
            self.carriers.set_index("name")[["asm", "rpm"]]
            .rename_axis(columns="measure")
            .unstack()
            .to_frame("value")
            .reset_index()
        )
        if raw_df:
            return df
        import altair as alt

        chart = alt.Chart(df, title="Carrier Loads")
        bars = chart.mark_bar().encode(
            x=alt.X("name:N", title="Carrier"),
            y=alt.Y("value", stack=None, title="miles"),
            color="measure",
            tooltip=["name", "measure", alt.Tooltip("value", format=".4s")],
        )
        text = chart.mark_text(
            dx=0,
            dy=5,
            color="white",
            baseline="top",
        ).encode(
            x=alt.X("name:N"),
            y=alt.Y("value").stack(None),
            text=alt.Text("value:Q", format=".4s"),
        )
        fig = (
            (bars + text)
            .properties(
                width=400,
                height=300,
            )
            .configure_axis(
                labelFontSize=12,
                titleFontSize=12,
            )
            .configure_legend(
                titleFontSize=12,
                labelFontSize=15,
            )
        )
        if report:
            report.add_figure(fig)
        return fig

    def _fig_fare_class_mix(
        self, df: pd.DataFrame, label_threshold: float = 0.06, title=None
    ):
        import altair as alt

        label_threshold_value = (
            df.groupby("carrier").avg_sold.sum().max() * label_threshold
        )
        chart = alt.Chart(
            df, **({"title": title} if title else {})
        ).transform_calculate(
            halfsold="datum.avg_sold / 2.0",
        )
        bars = chart.mark_bar().encode(
            x=alt.X("carrier:N", title="Carrier"),
            y=alt.Y("avg_sold:Q", title="Seats").stack("zero"),
            color="booking_class",
            tooltip=[
                "carrier",
                "booking_class",
                alt.Tooltip("avg_sold", format=".2f"),
            ],
        )
        text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
            x=alt.X("carrier:N", title="Carrier"),
            y=alt.Y("avg_sold:Q", title="Seats").stack("zero"),
            text=alt.Text("avg_sold:Q", format=".2f"),
            opacity=alt.condition(
                f"datum.avg_sold < {label_threshold_value:.3f}",
                alt.value(0),
                alt.value(1),
            ),
            order=alt.Order("booking_class:N", sort="descending"),
        )
        return (
            (bars + text)
            .properties(
                width=400,
                height=300,
            )
            .configure_axis(
                labelFontSize=12,
                titleFontSize=12,
            )
            .configure_legend(
                titleFontSize=12,
                labelFontSize=15,
            )
        )

    @report_figure
    def fig_fare_class_mix(self, raw_df=False, label_threshold=0.06):
        df = self.fare_class_mix[["carrier", "booking_class", "avg_sold"]]
        if raw_df:
            return df
        return self._fig_fare_class_mix(
            df,
            label_threshold=label_threshold,
            title="Fare Class Mix",
        )

    @report_figure
    def fig_od_fare_class_mix(
        self, orig: str, dest: str, raw_df=False, label_threshold=0.06
    ):
        df = self.od_fare_class_mix[orig, dest][
            ["carrier", "booking_class", "avg_sold"]
        ]
        if raw_df:
            return df
        return self._fig_fare_class_mix(
            df, label_threshold=label_threshold, title=f"Fare Class Mix ({orig}-{dest})"
        )

    @property
    def raw_fare_class_mix(self) -> pd.DataFrame:
        """Raw data giving the fare class mix.

        This tidy dataframe contains these columns:

        - carrier (str)
        - booking_class (str)
        - avg_sold (float)
        """
        return self.fig_fare_class_mix(raw_df=True)

    @report_figure
    def fig_bookings_by_timeframe(
        self,
        by_carrier: bool | str = True,
        by_class: bool | str = False,
        raw_df: bool = False,
        errorbands: bool = False,
    ):
        if errorbands:
            if by_carrier is True:
                raise NotImplementedError("error bands for all airlines is messy")
            return self._fig_bookings_by_timeframe_errorband(
                by_carrier=by_carrier, raw_df=raw_df
            )

        def differs(x):
            return x.shift(-1, fill_value=0) - x

        def _summarize(x: pd.DataFrame, c: str):
            if "trial" not in x.columns:
                x = x.assign(trial=0)
            if by_class:
                y = (
                    x.groupby(["trial", "carrier", "class", "rrd"])[f"avg_{c}"]
                    .sum()
                    .unstack(["trial", "carrier", "class"])
                    .sort_index(ascending=False)
                    .apply(differs)
                    .stack(["carrier", "class"])
                    .aggregate(["mean", "sem"], axis=1)
                    .assign(
                        ci0=lambda x: np.maximum(x["mean"] - 1.96 * x["sem"], 0),
                        ci1=lambda x: x["mean"] + 1.96 * x["sem"],
                    )
                )
            else:
                y = (
                    x.groupby(["trial", "carrier", "rrd"])[f"avg_{c}"]
                    .sum()
                    .unstack(["trial", "carrier"])
                    .sort_index(ascending=False)
                    .apply(differs)
                    .stack("carrier")
                    .aggregate(["mean", "sem"], axis=1)
                    .assign(
                        ci0=lambda x: np.maximum(x["mean"] - 1.96 * x["sem"], 0),
                        ci1=lambda x: x["mean"] + 1.96 * x["sem"],
                    )
                )
            return pd.concat({c: y}, names=["paxtype"])

        df0 = _summarize(self.bookings_by_timeframe, "business")
        df1 = _summarize(self.bookings_by_timeframe, "leisure")
        df = (
            pd.concat([df0, df1], axis=0)
            .rename(columns={"mean": "sold"})
            .reset_index()
            .query("(rrd>0) & (sold>0)")
        )
        title = "Bookings by Timeframe"
        if by_class is True:
            title = "Bookings by Timeframe and Booking Class"
        title_annot = []
        if not by_carrier:
            g = ["rrd", "paxtype"]
            if by_class:
                g += ["class"]
            df = df.groupby(g)[["sold", "ci0", "ci1"]].sum().reset_index()
        if isinstance(by_carrier, str):
            df = df[df["carrier"] == by_carrier]
            df = df.drop(columns=["carrier"])
            title_annot.append(by_carrier)
            by_carrier = False
        if isinstance(by_class, str):
            df = df[df["class"] == by_class]
            df = df.drop(columns=["class"])
            title_annot.append(f"Class {by_class}")
            by_class = False
        if title_annot:
            title = f"{title} ({', '.join(title_annot)})"
        if raw_df:
            return df

        import altair as alt

        if by_carrier:
            color = "carrier:N"
            color_title = "Carrier"
        elif by_class:
            color = "class:N"
            color_title = "Booking Class"
        else:
            color = "paxtype:N"
            color_title = "Passenger Type"

        if by_class:
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    color=alt.Color(color).title(color_title),
                    x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                    y=alt.Y("sold"),
                    tooltip=(
                        [alt.Tooltip("carrier").title("Carrier")] if by_carrier else []
                    )
                    + [
                        alt.Tooltip("paxtype", title="Passenger Type"),
                        alt.Tooltip("rrd", title="DfD"),
                        alt.Tooltip("sold", format=".2f"),
                    ],
                )
                .properties(
                    width=500,
                    height=200,
                )
                .facet(
                    row=alt.Row("paxtype:N", title="Passenger Type"),
                    title=title,
                )
                .configure_title(fontSize=18)
            )
        else:
            chart = (
                alt.Chart(df, title=title)
                .mark_line()
                .encode(
                    color=alt.Color(color).title(color_title),
                    x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                    y=alt.Y("sold") if by_class else "sold",
                    strokeDash=alt.StrokeDash("paxtype").title("Passenger Type"),
                    tooltip=(
                        [alt.Tooltip("carrier").title("Carrier")] if by_carrier else []
                    )
                    + [
                        alt.Tooltip("paxtype", title="Passenger Type"),
                        alt.Tooltip("rrd", title="DfD"),
                        alt.Tooltip("sold", format=".2f"),
                    ],
                )
                .properties(
                    width=500,
                    height=300,
                )
                .configure_axis(
                    labelFontSize=12,
                    titleFontSize=12,
                )
                .configure_legend(
                    titleFontSize=12,
                    labelFontSize=15,
                )
            )
        return chart

    def _fig_bookings_by_timeframe_errorband(
        self, by_carrier: bool | str = True, raw_df=False
    ):
        def differs(x):
            return x.shift(-1, fill_value=0) - x

        b = self.bookings_by_timeframe

        def _summarize(x, c):
            y = (
                x.groupby(["trial", "carrier", "rrd"])[f"avg_{c}"]
                .sum()
                .unstack(["trial", "carrier"])
                .sort_index(ascending=False)
                .apply(differs)
                .stack("carrier")
                .aggregate(["mean", "sem"], axis=1)
                .assign(
                    ci0=lambda x: x["mean"] - 1.96 * x["sem"],
                    ci1=lambda x: x["mean"] + 1.96 * x["sem"],
                )
            )
            return pd.concat({c: y}, names=["paxtype"])

        df0 = _summarize(b, "business")
        df1 = _summarize(b, "leisure")
        df = (
            pd.concat([df0, df1], axis=0)
            .rename(columns={"mean": "sold"})
            .reset_index()
            .query("rrd>0")
        )
        if not by_carrier:
            df = (
                df.groupby(["rrd", "paxtype"])[["sold", "ci0", "ci1"]]
                .sum()
                .reset_index()
            )
        if isinstance(by_carrier, str):
            df = df[df["carrier"] == by_carrier]
            df = df.drop(columns=["carrier"])
            by_carrier = False
        if raw_df:
            return df
        import altair as alt

        chart = alt.Chart(df)
        lines = chart.mark_line().encode(
            color=alt.Color("carrier:N" if by_carrier else "paxtype").title(
                "Carrier" if by_carrier else "Passenger Type"
            ),
            x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
            y="sold",
            strokeDash=alt.StrokeDash("paxtype").title("Passenger Type"),
            tooltip=([alt.Tooltip("carrier").title("Carrier")] if by_carrier else [])
            + [
                alt.Tooltip("paxtype", title="Passenger Type"),
                alt.Tooltip("rrd", title="DfD"),
                alt.Tooltip("sold", format=".2f"),
            ],
        )
        bands = chart.mark_errorband().encode(
            color=alt.Color(
                "carrier:N" if by_carrier else "paxtype",
                title="Carrier" if by_carrier else "Passenger Type",
            ),
            x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
            y="ci0",
            y2="ci1",
            strokeDash=alt.StrokeDash("paxtype").title("Passenger Type"),
        )

        return (
            (lines + bands)
            .properties(
                width=500,
                height=300,
            )
            .configure_axis(
                labelFontSize=12,
                titleFontSize=12,
            )
            .configure_legend(
                titleFontSize=12,
                labelFontSize=15,
            )
        )

    def _fig_carrier_load_factors(
        self,
        raw_df: bool,
        load_measure: str,
        measure_name: str,
        measure_format: str = ".2f",
        orient: Literal["h", "v"] = "h",
        title: str | None = None,
    ):
        df = self.load_factors[["carrier", load_measure]]
        if raw_df:
            return df
        import altair as alt

        chart = alt.Chart(df)
        if orient == "v":
            bars = chart.mark_bar().encode(
                x=alt.X("carrier:N", title="Carrier"),
                y=alt.Y(f"{load_measure}:Q", title=measure_name).stack("zero"),
                tooltip=[
                    alt.Tooltip("carrier", title="Carrier"),
                    alt.Tooltip(
                        f"{load_measure}:Q", title=measure_name, format=measure_format
                    ),
                ],
            )
            text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
                x=alt.X("carrier:N", title="Carrier"),
                y=alt.Y(f"{load_measure}:Q", title=measure_name).stack("zero"),
                text=alt.Text(f"{load_measure}:Q", format=measure_format),
            )
        else:
            bars = chart.mark_bar().encode(
                y=alt.Y("carrier:N", title="Carrier"),
                x=alt.X(f"{load_measure}:Q", title=measure_name).stack("zero"),
                tooltip=[
                    alt.Tooltip("carrier", title="Carrier"),
                    alt.Tooltip(
                        f"{load_measure}:Q", title=measure_name, format=measure_format
                    ),
                ],
            )
            text = chart.mark_text(
                dx=-5, dy=0, color="white", baseline="middle", align="right"
            ).encode(
                y=alt.Y("carrier:N", title="Carrier"),
                x=alt.X(f"{load_measure}:Q", title=measure_name).stack("zero"),
                text=alt.Text(f"{load_measure}:Q", format=measure_format),
            )
        fig = (
            (bars + text)
            .properties(
                width=500,
                height=10 + 20 * len(df),
            )
            .configure_axis(
                labelFontSize=12,
                titleFontSize=12,
            )
            .configure_legend(
                titleFontSize=12,
                labelFontSize=15,
            )
        )
        if title:
            fig.title = title
        return fig

    @report_figure
    def fig_carrier_load_factors(
        self, raw_df=False, load_measure: Literal["sys_lf", "avg_lf"] = "sys_lf"
    ):
        measure_name = (
            "System Load Factor" if load_measure == "sys_lf" else "Leg Load Factor"
        )
        return self._fig_carrier_load_factors(
            raw_df,
            load_measure,
            measure_name,
            title=f"Carrier {measure_name}s",
        )

    @report_figure
    def fig_carrier_revenues(self, raw_df=False):
        return self._fig_carrier_load_factors(
            raw_df, "avg_rev", "Average Revenue", "$.4s", title="Carrier Revenues"
        )
