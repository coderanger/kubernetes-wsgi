"""
Run your existing WSGI application using `python -m kubernetes_wsgi myapp`.
"""

import importlib
import sys

# This is a fake import, only used during type checking.
from typing import TYPE_CHECKING, Optional

from .server import serve


if TYPE_CHECKING:
    from wsgiref.types import WSGIApplication


def load_application(app_str: str) -> "WSGIApplication":
    func_name = None  # type: Optional[str]
    if ":" in app_str:
        mod_name, func_name = app_str.split(":", 1)
    else:
        mod_name = app_str
    mod = importlib.import_module(mod_name)
    if func_name is None:
        # Auto-detection behavior.
        application = getattr(mod, "application", None)
        if application is None:
            application = getattr(mod, "app", None)
        if application is None:
            raise ValueError(
                "Unable to find WSGI application function automatically,"
                "please specify {}:mywsgifunc".format(mod_name)
            )
    else:
        application = getattr(mod, func_name)
    return application


def main():
    app, port = (sys.argv[1:] + ([None] * 2))[:2]
    if app is None:
        app = "wsgi"
    if port is None:
        port = 8000
    app = load_application(app)
    port = int(port)
    serve(app, port=port)


if __name__ == "__main__":
    main()
