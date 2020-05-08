import os.path
import subprocess
import sys
import time

import pytest
import requests


@pytest.fixture
def launch_server():
    procs = []

    def _inner(*args):
        if procs:
            raise ValueError("already started")
        proc = subprocess.Popen(
            [sys.executable, "-m", "kubernetes_wsgi"] + list(args),
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        procs.append(proc)
        # Wait a second to let it start up.
        time.sleep(1)
        return proc

    yield _inner

    for proc in procs:
        proc.terminate()
        proc.wait()
        proc.stdout.close()
        proc.stderr.close()


def test_app1(launch_server):
    p = launch_server("app1.wsgi")
    assert p.poll() is None
    r = requests.get("http://localhost:8000/")
    assert r.text == "Hello world\n"
    r = requests.get("http://localhost:9000/")
    assert "twisted_threadpool_idle_worker_count" in r.text


def test_app1_application(launch_server):
    p = launch_server("app1.wsgi:application")
    assert p.poll() is None
    r = requests.get("http://localhost:8000/")
    assert r.text == "Hello world\n"
    r = requests.get("http://localhost:9000/")
    assert "twisted_threadpool_idle_worker_count" in r.text


def test_app1_fail(launch_server):
    p = launch_server("app1.wsgi:notthere")
    assert p.poll() == 1


def test_app1_port(launch_server):
    p = launch_server("app1.wsgi", "--port", "8080")
    assert p.poll() is None
    r = requests.get("http://localhost:8080/")
    assert r.text == "Hello world\n"
    r = requests.get("http://localhost:9000/")
    assert "twisted_threadpool_idle_worker_count" in r.text
