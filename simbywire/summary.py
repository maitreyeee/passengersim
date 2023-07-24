import pandas as pd


class SummaryTables:
    def __init__(
        self,
        demands: pd.DataFrame | None = None,
        legs: pd.DataFrame | None = None,
        paths: pd.DataFrame | None = None,
        airlines: pd.DataFrame | None = None,
    ):
        self.demands = demands
        self.legs = legs
        self.paths = paths
        self.airlines = airlines

    def to_records(self):
        return {k: v.to_dict(orient="records") for (k, v) in self.__dict__.items()}

    def fig_airline_loads(self):
        """Figure showing ASM, RPM by airline."""
        import altair as alt

        return (
            alt.Chart(
                self.airlines.set_index("name")[["asm", "rpm"]]
                .rename_axis(columns="measure")
                .unstack()
                .to_frame("value")
                .reset_index()
            )
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
