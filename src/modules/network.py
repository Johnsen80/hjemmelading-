"""Small thread-based network worker shim.

This is intentionally lightweight: it runs a callable in a background
daemon thread and exposes two callback hooks: `on_finished(result)` and
`on_error(exception)`. It avoids any GUI-specific APIs so it can be used
from non-GUI contexts during triage and testing.
"""

from __future__ import annotations

import threading
import traceback
from typing import Any, Callable, Optional


class NetworkWorker:
    """Run `func(*args, **kwargs)` in a background thread.

    - `on_finished` will be called with the result when the function
      completes successfully.
    - `on_error` will be called with the exception if the function
      raises.
    """

    def __init__(
        self, func: Callable[..., Any], args: tuple = (), kwargs: Optional[dict] = None
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.on_finished: Optional[Callable[[Any], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        try:
            result = self.func(*self.args, **self.kwargs)
            if self.on_finished:
                try:
                    self.on_finished(result)
                except Exception:
                    # Swallow errors from callbacks to keep worker robust
                    pass
        except Exception as exc:  # pragma: no cover - best-effort error handling
            if self.on_error:
                try:
                    self.on_error(exc)
                except Exception:
                    pass
            else:
                # Last-resort logging if no error handler is wired.
                import logging

                logging.getLogger(__name__).debug(
                    "NetworkWorker error: %s\n%s", exc, traceback.format_exc()
                )

    def start(self) -> None:
        self._thread.start()


def run_in_thread(
    func: Callable[..., Any],
    args: tuple = (),
    kwargs: Optional[dict] = None,
    on_finished: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> NetworkWorker:
    worker = NetworkWorker(func, args=args, kwargs=kwargs)
    worker.on_finished = on_finished
    worker.on_error = on_error
    worker.start()
    return worker
