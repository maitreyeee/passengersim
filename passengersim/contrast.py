import altair as alt
import pandas as pd

from .summary import SummaryTables


def fig_bookings_by_timeframe(summaries, by_airline: bool | str = True, raw_df=False):
    summaries_ = {}
    for k, v in summaries.items():
        if isinstance(v, SummaryTables):
            summaries_[k] = v.fig_bookings_by_timeframe(
                by_airline=by_airline, raw_df=True
            )
        elif hasattr(v, "raw_bookings_by_timeframe"):
            summaries_[k] = v.raw_bookings_by_timeframe
        elif v is not None:
            summaries_[k] = v
    df = pd.concat(summaries_, names=["source"]).reset_index(level="source")

    return (
        alt.Chart(df.sort_values("source", ascending=False))
        .mark_line()
        .encode(
            color=alt.Color("source:N").title("Source"),
            x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
            y="sold",
            strokeDash=alt.StrokeDash("paxtype").title("Passenger Type"),
            strokeWidth=alt.StrokeWidth("source:N").title("Source"),
            tooltip=[
                alt.Tooltip("source").title("Source"),
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


def fig_carrier_load_factors(summaries, raw_df=False):
    summaries_ = {}
    for k, v in summaries.items():
        if isinstance(v, SummaryTables):
            summaries_[k] = v.fig_carrier_load_factors(raw_df=True)
        elif hasattr(v, "raw_carrier_load_factors"):
            summaries_[k] = v.raw_carrier_load_factors
        elif v is not None:
            summaries_[k] = v
    df = pd.concat(summaries_, names=["source"]).reset_index(level="source")
    if raw_df:
        return df

    chart = alt.Chart(df)
    bars = chart.mark_bar().encode(
        color=alt.Color("source:N", title="Source"),
        x=alt.X("source:N", title=None),
        y=alt.Y("avg_lf:Q", title="Load Factor").stack("zero"),
        tooltip=[
            alt.Tooltip("source", title=None),
            alt.Tooltip("carrier", title="Carrier"),
            alt.Tooltip("avg_lf", title="Load Factor", format=".2f"),
        ],
    )
    text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
        x=alt.X("source:N", title=None),
        y=alt.Y("avg_lf:Q", title="Load Factor").stack("zero"),
        text=alt.Text("avg_lf:Q", format=".2f"),
    )
    return (
        (bars + text)
        .properties(
            width=25 + 25 * len(df),
            height=300,
        )
        .facet(
            column=alt.Column("carrier:N", title="Carrier"),
            title="Carrier Load Factors",
        )
    )


def fig_carrier_revenues(summaries, raw_df=False):
    summaries_ = {}
    for k, v in summaries.items():
        if isinstance(v, SummaryTables):
            summaries_[k] = v.fig_carrier_revenues(raw_df=True)
        elif hasattr(v, "raw_carrier_revenues"):
            summaries_[k] = v.raw_carrier_revenues
        elif v is not None:
            summaries_[k] = v
    df = pd.concat(summaries_, names=["source"]).reset_index(level="source")
    if raw_df:
        return df

    chart = alt.Chart(df)
    bars = chart.mark_bar().encode(
        color=alt.Color("source:N", title="Source"),
        x=alt.X("source:N", title=None),
        y=alt.Y("avg_rev:Q", title="Revenue ($)").stack("zero"),
        tooltip=[
            alt.Tooltip("source", title=None),
            alt.Tooltip("carrier", title="Carrier"),
            alt.Tooltip("avg_rev", title="Revenue ($)", format="$.4s"),
        ],
    )
    text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
        x=alt.X("source:N", title=None),
        y=alt.Y("avg_rev:Q", title="Revenue ($)").stack("zero"),
        text=alt.Text("avg_rev:Q", format="$.4s"),
    )
    return (
        (bars + text)
        .properties(
            width=25 + 25 * len(df),
            height=300,
        )
        .facet(
            column=alt.Column("carrier:N", title="Carrier"),
            title="Carrier Revenues",
        )
    )
