from threading import Event

from nexo.core.cancellation import check_cancelled, current_cancellation

"""Run application operations outside Qt's GUI thread; deliver via queued signals."""

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot


class _Signals(QObject):
    finished = Signal(int, object, object)


class _Worker(QRunnable):
    def __init__(self, identity: int, operation: Callable[[], Any]) -> None:
        super().__init__()
        self.identity = identity
        self.operation = operation
        self.cancelled = Event()
        self.signals = _Signals()

    @Slot()
    def run(self) -> None:
        context = current_cancellation.set(self.cancelled)
        try:
            check_cancelled()
            result = self.operation()
            check_cancelled()
        except Exception as error:  # noqa: BLE001 - Worker boundary must contain failures.
            self.signals.finished.emit(self.identity, None, error)
        else:
            self.signals.finished.emit(self.identity, result, None)
        finally:
            current_cancellation.reset(context)


class TaskRunner(QObject):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(2)
        self._counter = 0
        self._jobs: dict[
            int, tuple[_Worker, Callable[[Any, Exception | None], None]]
        ] = {}
        self._stopped = False

    def submit(
        self,
        operation: Callable[[], Any],
        callback: Callable[[Any, Exception | None], None],
    ) -> None:
        if self._stopped:
            return
        self._counter += 1
        worker = _Worker(self._counter, operation)
        worker.signals.finished.connect(
            self._deliver, Qt.ConnectionType.QueuedConnection
        )
        self._jobs[self._counter] = (worker, callback)
        self.pool.start(worker)

    @Slot(int, object, object)
    def _deliver(self, identity: int, result: Any, error: Exception | None) -> None:
        job = self._jobs.pop(identity, None)
        if job is not None and not self._stopped and not job[0].cancelled.is_set():
            job[1](result, error)

    def cancel(self) -> None:
        for worker, _callback in self._jobs.values():
            worker.cancelled.set()

    def stop(self) -> None:
        self._stopped = True
        self.cancel()

    def wait(self) -> None:
        self.pool.waitForDone()
