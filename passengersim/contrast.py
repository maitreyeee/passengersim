from typing import Literal

import altair as alt
import pandas as pd

from .reporting import report_figure


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


@report_figure
def fig_bookings_by_timeframe(
    summaries, by_carrier: bool | str = True, by_class: bool | str = False, raw_df=False
):
    if by_carrier is True and by_class is True:
        raise NotImplementedError("comparing by both class and carrier is messy")
    df = _assemble(
        summaries, "bookings_by_timeframe", by_carrier=by_carrier, by_class=by_class
    )
    source_order = list(summaries.keys())

    title = "Bookings by Timeframe"
    if by_class is True:
        title = "Bookings by Timeframe and Booking Class"
    title_annot = []
    if isinstance(by_carrier, str):
        title_annot.append(by_carrier)
    if isinstance(by_class, str):
        title_annot.append(f"Class {by_class}")
    if title_annot:
        title = f"{title} ({', '.join(title_annot)})"

    if raw_df:
        df.attrs["title"] = title
        return df

    if by_class:
        if isinstance(by_class, str):
            color = alt.Color("source:N", title="Source", sort=source_order).title(
                "Source"
            )
            tooltips = ()
        else:
            color = alt.Color("class:N").title("Booking Class")
            tooltips = (alt.Tooltip("class", title="Booking Class"),)
        return (
            alt.Chart(df.sort_values("source", ascending=False))
            .mark_bar()
            .encode(
                color=color,
                x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                xOffset=alt.XOffset("source:N", title="Source", sort=source_order),
                y=alt.Y("sold", stack=True),
                tooltip=[
                    alt.Tooltip("source:N", title="Source"),
                    alt.Tooltip("paxtype", title="Passenger Type"),
                    *tooltips,
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
    elif by_carrier is True:
        return (
            alt.Chart(df.sort_values("source", ascending=False))
            .mark_bar()
            .encode(
                color=alt.Color("carrier:N").title("Carrier"),
                x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                xOffset=alt.XOffset("source:N", title="Source", sort=source_order),
                y=alt.Y("sold", stack=True),
                tooltip=[
                    alt.Tooltip("source:N", title="Source"),
                    alt.Tooltip("paxtype", title="Passenger Type"),
                    alt.Tooltip("carrier", title="Carrier"),
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
        return (
            alt.Chart(df.sort_values("source", ascending=False), title=title)
            .mark_line()
            .encode(
                color=alt.Color("source:N", title="Source", sort=source_order),
                x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                y="sold",
                strokeDash=alt.StrokeDash("paxtype").title("Passenger Type"),
                strokeWidth=alt.StrokeWidth(
                    "source:N", title="Source", sort=source_order
                ),
                tooltip=[
                    alt.Tooltip("source:N", title="Source"),
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


def _fig_carrier_measure(
    df,
    source_order,
    load_measure: str,
    measure_name: str,
    measure_format: str = ".2f",
    orient: Literal["h", "v"] = "h",
    title: str | None = None,
    ratio: str | bool = False,
):
    against = source_order[0]
    if ratio:
        if isinstance(ratio, str):
            against = ratio
        df_ = df.set_index(["source", "carrier"])
        ratios = df_.div(df_.query(f"source == '{against}'").droplevel("source")) - 1.0
        ratios.columns = ["ratio"]
        df = df.join(ratios, on=["source", "carrier"])

    facet_kwargs = {}
    if title is not None:
        facet_kwargs["title"] = title
    chart = alt.Chart(df)
    tooltips = [
        alt.Tooltip("source", title=None),
        alt.Tooltip("carrier", title="Carrier"),
        alt.Tooltip(f"{load_measure}:Q", title=measure_name, format=measure_format),
    ]
    if ratio:
        tooltips.append(
            alt.Tooltip("ratio:Q", title=f"vs {against}", format=".3%"),
        )
    if orient == "v":
        bars = chart.mark_bar().encode(
            color=alt.Color("source:N", title="Source"),
            x=alt.X("source:N", title=None, sort=source_order),
            y=alt.Y(f"{load_measure}:Q", title=measure_name).stack("zero"),
            tooltip=tooltips,
        )
        text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
            x=alt.X("source:N", title=None, sort=source_order),
            y=alt.Y(f"{load_measure}:Q", title=measure_name).stack("zero"),
            text=alt.Text(f"{load_measure}:Q", format=measure_format),
        )
        return (
            (bars + text)
            .properties(
                width=55 * len(source_order),
                height=300,
            )
            .facet(column=alt.Column("carrier:N", title="Carrier"), **facet_kwargs)
            .configure_title(fontSize=18)
        )
    else:
        bars = chart.mark_bar().encode(
            color=alt.Color("source:N", title="Source"),
            y=alt.Y("source:N", title=None, sort=source_order),
            x=alt.X(f"{load_measure}:Q", title=measure_name).stack("zero"),
            tooltip=tooltips,
        )
        text = chart.mark_text(
            dx=-5, dy=0, color="white", baseline="middle", align="right"
        ).encode(
            y=alt.Y("source:N", title=None, sort=source_order),
            x=alt.X(f"{load_measure}:Q", title=measure_name).stack("zero"),
            text=alt.Text(f"{load_measure}:Q", format=measure_format),
        )
        return (
            (bars + text)
            .properties(
                width=500,
                height=10 + 20 * len(source_order),
            )
            .facet(row=alt.Row("carrier:N", title="Carrier"), **facet_kwargs)
            .configure_title(fontSize=18)
        )


@report_figure
def fig_carrier_revenues(
    summaries,
    raw_df=False,
    orient: Literal["h", "v"] = "h",
    ratio: str | bool = True,
):
    df = _assemble(summaries, "carrier_revenues")
    source_order = list(summaries.keys())
    if raw_df:
        df.attrs["title"] = "Carrier Revenues"
        return df
    return _fig_carrier_measure(
        df,
        source_order,
        load_measure="avg_rev",
        measure_name="Revenue ($)",
        measure_format="$.4s",
        orient=orient,
        title="Carrier Revenues",
        ratio=ratio,
    )


@report_figure
def fig_carrier_load_factors(
    summaries,
    raw_df=False,
    load_measure: Literal["sys_lf", "avg_lf"] = "sys_lf",
    orient: Literal["h", "v"] = "h",
    ratio: str | bool = True,
):
    measure_name = {"sys_lf": "System Load Factor", "avg_lf": "Leg Load factor"}.get(
        load_measure, "Load Factor"
    )
    df = _assemble(summaries, "carrier_load_factors", load_measure=load_measure)
    source_order = list(summaries.keys())
    if raw_df:
        df.attrs["title"] = f"Carrier {measure_name}s"
        return df
    return _fig_carrier_measure(
        df,
        source_order,
        load_measure=load_measure,
        measure_name=measure_name,
        measure_format=".2f",
        orient=orient,
        title=f"Carrier {measure_name}s",
        ratio=ratio,
    )


@report_figure
def fig_fare_class_mix(summaries, raw_df=False, label_threshold=0.06):
    df = _assemble(summaries, "fare_class_mix")
    source_order = list(summaries.keys())
    if raw_df:
        df.attrs["title"] = "Carrier Fare Class Mix"
        return df
    import altair as alt

    label_threshold_value = (
        df.groupby(["carrier", "source"]).avg_sold.sum().max() * label_threshold
    )
    chart = alt.Chart(df).transform_calculate(
        halfsold="datum.avg_sold / 2.0",
    )
    bars = chart.mark_bar().encode(
        x=alt.X("source:N", title="Source", sort=source_order),
        y=alt.Y("avg_sold:Q", title="Seats").stack("zero"),
        color="booking_class",
        tooltip=[
            "source",
            "booking_class",
            alt.Tooltip("avg_sold", format=".2f"),
        ],
    )
    text = chart.mark_text(dx=0, dy=3, color="white", baseline="top").encode(
        x=alt.X("source:N", title="Source", sort=source_order),
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


@report_figure
def fig_leg_forecasts(summaries, raw_df=False, by_flt_no=None):
    df = _assemble(summaries, "leg_forecasts", by_flt_no=by_flt_no)
    list(summaries.keys())
    if raw_df:
        df.attrs["title"] = "Average Leg Forecasts"
        return df
    import altair as alt

    if isinstance(by_flt_no, int):
        return (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                y=alt.Y("demand_fcst:Q", title="Avg Demand Forecast"),
                color="booking_class:N",
                strokeDash=alt.StrokeDash("source:N", title="Source"),
                strokeWidth=alt.StrokeWidth("source:N", title="Source"),
            )
        )
    else:
        return (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("rrd:O").scale(reverse=True).title("Days from Departure"),
                y=alt.Y("demand_fcst:Q", title="Avg Demand Forecast"),
                color="booking_class:N",
                strokeDash=alt.StrokeDash("source:N", title="Source"),
                strokeWidth=alt.Size("source:N", title="Source"),
            )
            .facet(
                facet="flt_no:N",
                columns=3,
            )
        )
