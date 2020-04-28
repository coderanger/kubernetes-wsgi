import logging

# This is a fake import, only used during type checking.
from typing import TYPE_CHECKING, Callable

from prometheus_client import REGISTRY  # type: ignore
from prometheus_client.twisted import MetricsResource  # type: ignore
from twisted import logger  # type: ignore
from twisted.internet import reactor  # type: ignore
from twisted.internet.endpoints import TCP4ServerEndpoint  # type: ignore
from twisted.internet.protocol import Factory  # type: ignore
from twisted.logger import STDLibLogObserver  # type: ignore
from twisted.python import threadpool  # type: ignore
from twisted.web.http import Request, proxiedLogFormatter  # type: ignore
from twisted.web.server import Site  # type: ignore
from twisted.web.wsgi import WSGIResource  # type: ignore

from .metrics import TwistedThreadPoolCollector


if TYPE_CHECKING:
    from wsgiref.types import WSGIApplication


LogFormatter = Callable[[str, Request], str]


class KubernetesWSGISite(Site):
    """Extension to Site to ignore heath checks for access logging."""

    def __init__(self, health_check_path: str, *args, **kwargs):
        self.__health_check_path = health_check_path
        super().__init__(*args, **kwargs)

    def log(self, request):
        path = request.path.decode()
        if path != self.__health_check_path:
            return super().log(request)


class MetricsSite(Site):
    """Extension to Site to never produce access logs."""

    def log(_self, _):
        pass


def serve(
    application: "WSGIApplication",
    port: int = 8000,
    metrics_port: int = 9000,
    access_log_formatter: LogFormatter = proxiedLogFormatter,
    health_check_path: str = "/healthz",
):
    # Quiet the Twisted factory logging.
    Factory.noisy = False

    # Start logging.
    logging.basicConfig(level=logging.INFO)
    observers = [STDLibLogObserver()]
    logger.globalLogBeginner.beginLoggingTo(observers)

    # Create the server.
    pool = threadpool.ThreadPool()
    reactor.callWhenRunning(pool.start)
    _listen_wsgi(
        reactor,
        pool,
        application,
        port,
        access_log_formatter,
        health_check_path,
    )
    _listen_metrics(reactor, metrics_port)

    # Register the metrics collector.
    REGISTRY.register(TwistedThreadPoolCollector(pool))

    # Start the main loop.
    reactor.run()

    # Clean up when exiting.
    pool.stop()


def _listen_wsgi(
    reactor,
    pool,
    application: "WSGIApplication",
    port: int,
    access_log_formatter: LogFormatter,
    health_check_path: str,
) -> None:
    """Listen for the WSGI application."""
    wsgi_resource = WSGIResource(reactor, pool, application)
    wsgi_site = KubernetesWSGISite(
        health_check_path, wsgi_resource, logFormatter=access_log_formatter
    )
    wsgi_endpoint = TCP4ServerEndpoint(reactor, port)
    wsgi_endpoint.listen(wsgi_site)


def _listen_metrics(reactor, port: int) -> None:
    """Listen for serving Prometheus metrics."""
    metrics_resource = MetricsResource()
    metrics_site = MetricsSite(metrics_resource)
    metrics_endpoint = TCP4ServerEndpoint(reactor, port)
    metrics_endpoint.listen(metrics_site)
