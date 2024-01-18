import sys
from typing import Optional

from .exceptions import FatalError


def get_current_window_windows() -> Optional[dict]:
    from . import windows
    from . import regex as regex_module  # Renomeie a variável para evitar conflito

    window_handle = windows.get_active_window_handle()
    try:
        app = windows.get_app_name(window_handle)
    except Exception:  
        # try with wmi method
        app = windows.get_app_name_wmi(window_handle)

    title = windows.get_window_title(window_handle)

    try:
        path = windows.get_app_path(window_handle)
    except Exception:  
        # try with wmi method
        path = windows.get_app_path_wmi(window_handle)

    file_path = windows.get_file_path(window_handle)
    
    regex_result = regex_module.regex(title) 
    
    if app is None:
        app = "unknown"
    if title is None:
        title = "unknown"
    if path is None:
        path = "unknown"
    if file_path is None:
        file_path = "unknown"

    return {"app": app, "title": title, "app_path": path, "file_path": file_path, "regex": regex_result}

def get_current_window(strategy: Optional[str] = None) -> Optional[dict]:
    """
    :raises FatalError: if a fatal error occurs (e.g. unsupported platform, X server closed)
    """

    if sys.platform in ["win32", "cygwin"]:
        return get_current_window_windows()
    else:
        raise FatalError(f"Unknown platform: {sys.platform}")