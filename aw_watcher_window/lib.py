import sys
from typing import Optional

from .exceptions import FatalError

def get_current_window() -> Optional[dict]:
    from . import windows

    window_handle = windows.get_active_window_handle()
    try:
        app = windows.get_app_name(window_handle)
    except Exception:  # TODO: narrow down the exception
        # try with wmi method
        app = windows.get_app_name_wmi(window_handle)

    title = windows.get_window_title(window_handle)

    try:
        path = windows.get_app_path(window_handle)
    except Exception:  # TODO: narrow down the exception
        # try with wmi method
        path = windows.get_app_path_wmi(window_handle)

    if app is None:
        app = "unknown"
    if title is None:
        title = "unknown"
    if path is None:
        path = "unknown"

    return {"app": app, "title": title, "path": path}