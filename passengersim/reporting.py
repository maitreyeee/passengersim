import xmle
from altair.utils.schemapi import UndefinedType


class Report(xmle.Reporter):
    def __init__(self, title=None, short_title=None):
        super().__init__(title=title, short_title=short_title)
        self._numbered_figure = xmle.NumberedCaption("Figure", level=2, anchor=True)
        self._numbered_table = xmle.NumberedCaption("Table", level=2, anchor=True)

    def add_section(self, title):
        self.__ilshift__(None)  # clear prior seen_html
        self.append(f"# {title}")
        return self

    def add_figure(self, title, fig=None):
        stolen_title = False
        if fig is None:
            fig = title
            try:
                title = fig.title
            except AttributeError as err:
                raise ValueError("figure has no title attribute") from err
            if isinstance(title, UndefinedType):
                raise ValueError("figure has no title defined")
            fig.title = ""
            stolen_title = True
        self << self._numbered_figure(title)
        self.__ilshift__(fig)
        if stolen_title:
            fig.title = title
        return fig

    def add_table(self, title, tbl):
        self << self._numbered_table(title)
        self.__ilshift__(tbl)
        return tbl


def report_figure(func):
    def report_figure_wrapper(*args, report=None, **kwargs):
        fig = func(*args, **kwargs)
        if report is not None:
            report.add_figure(fig)
        return fig

    return report_figure_wrapper
