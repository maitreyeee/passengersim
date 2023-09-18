try:
    import xmle
    from altair.utils.schemapi import UndefinedType
except ImportError:
    import warnings

    warnings.warn("reporting dependencies (xmle, altair) not installed", stacklevel=2)
else:
    from .report import Report


def report_figure(func):
    def report_figure_wrapper(*args, report=None, **kwargs):
        fig = func(*args, **kwargs)
        if report is not None:
            report.add_figure(fig)
        return fig

    return report_figure_wrapper
