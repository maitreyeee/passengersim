import pandas as pd


class SummaryTables:
    def __init__(
        self,
        demands: pd.DataFrame | None = None,
        legs: pd.DataFrame | None = None,
        paths: pd.DataFrame | None = None,
        airlines: pd.DataFrame | None = None,
        fare_class_mix: pd.DataFrame | None = None,
        load_factors: pd.DataFrame | None = None,
        bookings_by_timeframe: pd.DataFrame | None = None,
        total_demand: float | None = None,
    ):
        self.demands = demands
        self.legs = legs
        self.paths = paths
        self.airlines = airlines
        self.fare_class_mix = fare_class_mix
        self.load_factors = load_factors
        self.bookings_by_timeframe = bookings_by_timeframe
        self.total_demand = total_demand

    def to_records(self):
        return {k: v.to_dict(orient="records") for (k, v) in self.__dict__.items()}

    def fig_airline_loads(self, raw_df=False):
        """Figure showing ASM, RPM by airline."""
        df = (
            self.airlines.set_index("name")[["asm", "rpm"]]
            .rename_axis(columns="measure")
            .unstack()
            .to_frame("value")
            .reset_index()
        )
        if raw_df:
            return df
        import altair as alt

        chart = alt.Chart(df)
        bars = chart.mark_bar().encode(
            x=alt.X("name:N", title="Airline"),
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

    def fig_fare_class_mix(self, raw_df=False, label_threshold=0.06):
        df = self.fare_class_mix[["carrier", "booking_class", "avg_sold"]]
        if raw_df:
            return df
        import altair as alt

        label_threshold_value = (
            df.groupby("carrier").avg_sold.sum().max() * label_threshold
        )
        chart = alt.Chart(df).transform_calculate(
            halfsold="datum.avg_sold / 2.0",
        )
        bars = chart.mark_bar().encode(
            x=alt.X("carrier:N", title="Airline"),
            y=alt.Y("avg_sold:Q", title="Seats").stack("zero"),
            color="booking_class",
            tooltip=[
                "carrier",
                "booking_class",
                alt.Tooltip("avg_sold", format=".2f"),
            ],
        )
        text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
            x=alt.X("carrier:N", title="Airline"),
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

    @property
    def raw_fare_class_mix(self) -> pd.DataFrame:
        """Raw data giving the fare class mix.

        This tidy dataframe contains these columns:

        - carrier (str)
        - booking_class (str)
        - avg_sold (float)
        """
        return self.fig_fare_class_mix(raw_df=True)

    def fig_bookings_by_timeframe(
        self, by_airline: bool | str = True, raw_df=False, errorbands=False
    ):
        if errorbands:
            if by_airline is True:
                raise NotImplementedError("error bands for all airlines is messy")
            return self._fig_bookings_by_timeframe_errorband(
                by_airline=by_airline, raw_df=raw_df
            )

        def differs(x):
            return x.shift(-1, fill_value=0) - x

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

        df0 = _summarize(self.bookings_by_timeframe, "business")
        df1 = _summarize(self.bookings_by_timeframe, "leisure")
        df = (
            pd.concat([df0, df1], axis=0)
            .rename(columns={"mean": "sold"})
            .reset_index()
            .query("rrd>0")
        )
        if not by_airline:
            df = (
                df.groupby(["rrd", "paxtype"])[["sold", "ci0", "ci1"]]
                .sum()
                .reset_index()
            )
        if isinstance(by_airline, str):
            df = df[df["carrier"] == by_airline]
            df = df.drop(columns=["carrier"])
            by_airline = False
        if raw_df:
            return df

        import altair as alt

        return (
            alt.Chart(df)
            .mark_line()
            .encode(
                color=alt.Color("carrier:N" if by_airline else "paxtype").title(
                    "Carrier" if by_airline else "Passenger Type"
                ),
                x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                y="sold",
                strokeDash=alt.StrokeDash("paxtype").title("Passenger Type"),
                tooltip=(
                    [alt.Tooltip("carrier").title("Carrier")] if by_airline else []
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

    def _fig_bookings_by_timeframe_errorband(
        self, by_airline: bool | str = True, raw_df=False
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
        if not by_airline:
            df = (
                df.groupby(["rrd", "paxtype"])[["sold", "ci0", "ci1"]]
                .sum()
                .reset_index()
            )
        if isinstance(by_airline, str):
            df = df[df["carrier"] == by_airline]
            df = df.drop(columns=["carrier"])
            by_airline = False
        if raw_df:
            return df
        import altair as alt

        chart = alt.Chart(df)
        lines = chart.mark_line().encode(
            color=alt.Color("carrier:N" if by_airline else "paxtype").title(
                "Carrier" if by_airline else "Passenger Type"
            ),
            x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
            y="sold",
            strokeDash=alt.StrokeDash("paxtype").title("Passenger Type"),
            tooltip=([alt.Tooltip("carrier").title("Carrier")] if by_airline else [])
            + [
                alt.Tooltip("paxtype", title="Passenger Type"),
                alt.Tooltip("rrd", title="DfD"),
                alt.Tooltip("sold", format=".2f"),
            ],
        )
        bands = chart.mark_errorband().encode(
            color=alt.Color(
                "carrier:N" if by_airline else "paxtype",
                title="Carrier" if by_airline else "Passenger Type",
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

    def fig_carrier_load_factors(self, raw_df=False):
        df = self.load_factors[["carrier", "avg_lf"]]
        if raw_df:
            return df
        import altair as alt

        chart = alt.Chart(df)
        bars = chart.mark_bar().encode(
            x=alt.X("carrier:N", title="Carrier"),
            y=alt.Y("avg_lf:Q", title="Load Factor").stack("zero"),
            tooltip=[
                alt.Tooltip("carrier", title="Carrier"),
                alt.Tooltip("avg_lf", title="Load Factor", format=".2f"),
            ],
        )
        text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
            x=alt.X("carrier:N", title="Carrier"),
            y=alt.Y("avg_lf:Q", title="Load Factor").stack("zero"),
            text=alt.Text("avg_lf:Q", format=".2f"),
        )
        return (
            (bars + text)
            .properties(
                width=50 + 75 * len(df),
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

    def fig_carrier_revenues(self, raw_df=False):
        df = self.load_factors[["carrier", "avg_rev"]]
        if raw_df:
            return df
        import altair as alt

        chart = alt.Chart(df)
        bars = chart.mark_bar().encode(
            x=alt.X("carrier:N", title="Carrier"),
            y=alt.Y("avg_rev:Q", title="Revenue").stack("zero"),
            tooltip=[
                alt.Tooltip("carrier", title="Carrier"),
                alt.Tooltip("avg_rev", title="Revenue", format="$.4s"),
            ],
        )
        text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
            x=alt.X("carrier:N", title="Carrier"),
            y=alt.Y("avg_rev:Q", title="Revenue").stack("zero"),
            text=alt.Text("avg_rev:Q", format="$.4s"),
        )
        return (
            (bars + text)
            .properties(
                width=50 + 75 * len(df),
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
