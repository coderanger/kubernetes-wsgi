import os
import signal
import time

import pytest
import requests

from kubernetes_wsgi.server import serve


@pytest.fixture
def launch_server():
    pids = []

    def _inner(*args, **kwargs):
        if pids:
            raise ValueError("already started")
        pid = os.fork()
        if pid == 0:
            serve(*args, **kwargs)
            os._exit(0)
        else:
            pids.append(pid)
            # Wait a second to let it start up.
            time.sleep(1)

    yield _inner

    for pid in pids:
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)


def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    yield b"Hello world\n"


def test_defaults(launch_server):
    launch_server(application)
    r = requests.get("http://localhost:8000/")
    assert r.text == "Hello world\n"
    r = requests.get("http://localhost:9000/")
    assert "twisted_threadpool_idle_worker_count" in r.text


def test_ports(launch_server):
    launch_server(application, port=8080, metrics_port=8081)
    r = requests.get("http://localhost:8080/")
    assert r.text == "Hello world\n"
    r = requests.get("http://localhost:8081/")
    assert "twisted_threadpool_idle_worker_count" in r.text
