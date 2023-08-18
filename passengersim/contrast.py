import altair as alt
import pandas as pd


def fig_bookings_by_timeframe(summaries):
    df = pd.concat(summaries, names=["source"]).reset_index(level="source")

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
