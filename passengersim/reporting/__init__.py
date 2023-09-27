import pandas as pd

try:
    import xmle
    from altair.utils.schemapi import UndefinedType
except ImportError:
    import warnings

    warnings.warn("reporting dependencies (xmle, altair) not installed", stacklevel=2)
else:
    from .report import Report


def report_figure(func):
    def report_figure_wrapper(*args, report=None, trace=None, **kwargs):
        fig = func(*args, **kwargs)
        if report is not None:
            report.add_figure(fig)
        if trace is not None:
            trace_sheetname = None
            if isinstance(trace, tuple):
                if len(trace) > 1:
                    trace_sheetname = trace[1]
                if len(trace) > 0:
                    trace = trace[0]
                else:
                    raise ValueError("trace is a zero-length tuple")
            kwargs["raw_df"] = True
            raw: pd.DataFrame = func(*args, **kwargs)
            if isinstance(trace, pd.ExcelWriter):
                if trace_sheetname is None:
                    sheet_base = func.__name__ or "Sheet"
                    sheet_num = 1
                    while f"{sheet_base}_{sheet_num}" in trace.sheets:
                        sheet_num += 1
                    trace_sheetname = f"{sheet_base}_{sheet_num}"
                startrow = 0
                if "title" in raw.attrs:
                    startrow += 2
                raw.to_excel(
                    trace, sheet_name=trace_sheetname, index=False, startrow=startrow
                )
                if "title" in raw.attrs:
                    worksheet = trace.sheets[trace_sheetname]
                    worksheet.write_string(0, 0, raw.attrs["title"])
            else:
                raise NotImplementedError("only tracing to excel is implemented")
        return fig

    return report_figure_wrapper
