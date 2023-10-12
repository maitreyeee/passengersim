import time

try:
    from rich.progress import Progress
except ImportError:
    Progress = None


class DummyProgressBar:
    """Dummy for when rich is not installed."""

    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def __enter__(self) -> "ProgressBar":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def tick(self, refresh=False):
        pass


class ProgressBar:
    def __init__(self, label="samples", total=100, refresh_per_second=10):
        self.label = label
        self.total = total
        self.last_update = 0
        self.refresh_freq = 1.0 / refresh_per_second
        self.progress = Progress(transient=True)
        self.task = self.progress.add_task(self.label, total=self.total)

    def start(self) -> "ProgressBar":
        self.progress.start()
        return self

    def stop(self) -> None:
        self.progress.stop()

    def __enter__(self) -> "ProgressBar":
        self.progress.start()
        self.start_time = self.progress.get_time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.progress.stop()
        current_time = self.progress.get_time()
        elapsed_time = current_time - self.start_time
        happened = "Completed"
        if exc_type is KeyboardInterrupt:
            happened = "Aborted"
        elif exc_type is not None:
            happened = "Errored"
        self.progress.print(f"Task {happened} after {elapsed_time:,.2f} seconds")

    def tick(self, refresh=False):
        self.progress.update(self.task, advance=1)
        now = time.time()
        if refresh or (now - self.last_update > self.refresh_freq):
            self.last_update = now
            self.progress.refresh()


if Progress is None:
    ProgressBar = DummyProgressBar  # noqa: F811
