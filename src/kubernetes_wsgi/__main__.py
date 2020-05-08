"""
Run your existing WSGI application using `python -m kubernetes_wsgi myapp`.
"""

import argparse
import importlib
import sys

# This is a fake import, only used during type checking.
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Text

from .server import serve


if TYPE_CHECKING:
    from wsgiref.types import WSGIApplication


def parse_args(argv: Sequence[Text]) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="kubernetes_wsgi",
        description="Start a kubernetes-wsgi web server",
    )
    parser.add_argument(
        "application",
        metavar="MODULE:APP",
        help="the WSGI application to run in a dotted import form "
        "(eg. myapp or myapp.wsgi) with an optional :function_name if needed",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port to run the web application on",
    )
    parser.add_argument(
        "--metrics-port",
        metavar="PORT",
        type=int,
        default=9000,
        help="port to run the Prometheus metrics on",
    )
    parser.add_argument(
        "--health-check-path",
        metavar="PATH",
        default="/healthz",
        help="URL path to the health check endpoint",
    )
    args = parser.parse_args(argv)
    return {
        "application": args.application,
        "port": args.port,
        "metrics_port": args.metrics_port,
        "health_check_path": args.health_check_path,
    }


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
    args = parse_args(sys.argv[1:])
    args["application"] = load_application(args["application"])
    serve(**args)


if __name__ == "__main__":
    main()
