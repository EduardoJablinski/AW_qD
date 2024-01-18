import sys
from typing import Optional

from .exceptions import FatalError

def get_current_window_windows() -> Optional[dict]:
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

def get_current_window(strategy: Optional[str] = None) -> Optional[dict]:
    """
    :raises FatalError: if a fatal error occurs (e.g. unsupported platform, X server closed)
    """

    if sys.platform in ["win32", "cygwin"]:
        return get_current_window_windows()
    else:
        raise FatalError(f"Unknown platform: {sys.platform}")