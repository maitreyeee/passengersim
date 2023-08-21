import altair as alt
import pandas as pd


def _assemble(summaries, base, **kwargs):
    summaries_ = {}
    for k, v in summaries.items():
        if (fun := getattr(v, f"fig_{base}", None)) is not None:
            summaries_[k] = fun(raw_df=True, **kwargs)
        elif (raw := getattr(v, f"raw_{base}", None)) is not None:
            summaries_[k] = raw
        elif isinstance(v, pd.DataFrame | pd.Series):
            summaries_[k] = v
    return pd.concat(summaries_, names=["source"]).reset_index(level="source")


def fig_bookings_by_timeframe(
    summaries, by_airline: bool | str = True, by_class: bool | str = False, raw_df=False
):
    df = _assemble(
        summaries, "bookings_by_timeframe", by_airline=by_airline, by_class=by_class
    )
    if raw_df:
        return df

    if by_class:
        return (
            alt.Chart(df.sort_values("source", ascending=False))
            .mark_bar()
            .encode(
                color=alt.Color("class:N").title("Booking Class"),
                x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                xOffset=alt.XOffset("source:N", title="Source"),
                y=alt.Y("sold", stack=True),
                tooltip=[
                    alt.Tooltip("source").title("Source"),
                    alt.Tooltip("paxtype", title="Passenger Type"),
                    alt.Tooltip("class", title="Booking Class"),
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
                title="Bookings by Class by Timeframe",
            )
            .configure_title(fontSize=18)
        )
    else:
        return (
            alt.Chart(
                df.sort_values("source", ascending=False), title="Bookings by Timeframe"
            )
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
            .configure_title(fontSize=18)
        )


def fig_carrier_load_factors(summaries, raw_df=False):
    df = _assemble(summaries, "carrier_load_factors")
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
        .configure_title(fontSize=18)
    )


def fig_carrier_revenues(summaries, raw_df=False):
    df = _assemble(summaries, "carrier_revenues")
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
        .configure_title(fontSize=18)
    )


def fig_fare_class_mix(summaries, raw_df=False, label_threshold=0.06):
    df = _assemble(summaries, "fare_class_mix")
    if raw_df:
        return df
    import altair as alt

    label_threshold_value = (
        df.groupby(["carrier", "source"]).avg_sold.sum().max() * label_threshold
    )
    chart = alt.Chart(df).transform_calculate(
        halfsold="datum.avg_sold / 2.0",
    )
    bars = chart.mark_bar().encode(
        x=alt.X("source:N", title="Airline"),
        y=alt.Y("avg_sold:Q", title="Seats").stack("zero"),
        color="booking_class",
        tooltip=[
            "source",
            "booking_class",
            alt.Tooltip("avg_sold", format=".2f"),
        ],
    )
    text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
        x=alt.X("source:N", title="Airline"),
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
            width=200,
            height=300,
        )
        .facet(
            column=alt.Column("carrier:N", title="Carrier"),
            title="Carrier Fare Class Mix",
        )
        .configure_title(fontSize=18)
    )
