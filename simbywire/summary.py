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

        return (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("name:N", title="Airline"),
                y=alt.Y("value:Q", stack=None, title="miles"),
                color="measure",
                tooltip=["name", "measure", alt.Tooltip("value", format=".4s")],
            )
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

    def fig_fare_class_mix(self, raw_df=False):
        df = self.fare_class_mix[["carrier", "booking_class", "avg_sold"]]
        if raw_df:
            return df
        import altair as alt

        return (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("carrier:N", title="Airline"),
                y=alt.Y("avg_sold:Q", stack=None, title="Seats"),
                color="booking_class",
                tooltip=[
                    "carrier",
                    "booking_class",
                    alt.Tooltip("avg_sold", format=".2f"),
                ],
            )
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

    def fig_bookings_by_timeframe(self, by_airline=True, raw_df=False):
        def differs(x):
            return x - x.shift(1, fill_value=0)

        b = self.bookings_by_timeframe
        df0 = (
            b.groupby(["carrier", "rrd"])["avg_business"]
            .sum()
            .unstack(0)
            .sort_index(ascending=False)
            .apply(differs)
            .stack()
            .rename("business")
        )
        df1 = (
            b.groupby(["carrier", "rrd"])["avg_leisure"]
            .sum()
            .unstack(0)
            .sort_index(ascending=False)
            .apply(differs)
            .stack()
            .rename("leisure")
        )
        df = (
            pd.concat([df0, df1], axis=1)
            .rename_axis(columns="paxtype")
            .stack()
            .rename("sold")
            .reset_index()
        )
        if not by_airline:
            df = df.groupby(["rrd", "paxtype"])[["sold"]].sum().reset_index()
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
                width=550,
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
