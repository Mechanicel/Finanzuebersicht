import logging
import threading
from collections.abc import Callable
from tkinter import Misc
from typing import Any

logger = logging.getLogger(__name__)


def run_in_background(
    tk_root: Misc,
    worker: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None] | None = None,
):
    """Run worker on a daemon thread and marshal completion back via tk.after."""

    def _runner():
        try:
            result = worker()
        except Exception as exc:  # defensive guard for UI stability
            logger.exception("Background worker crashed")
            if on_error is not None:
                tk_root.after(0, lambda: on_error(exc))
            return

        tk_root.after(0, lambda: on_success(result))

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    return thread
