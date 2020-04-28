# Kubernetes_WSGI

A wrapper for running your Python web application using Twisted in a way that works well for Kubernetes.

This also includes Prometheus metrics support.

## Quick Start

To install:

```
pip install kubernetes-wsgi
```

To launch your application:

```
python -m kubernetes_wsgi myapp 8000
```

where `myapp` is an importable module name containing your WSGI application function.

## Why Threads?

The gold standard for Python WSGI servers is Gunicorn, renowned for its multi-process execution mode for effcient concurrency despite the dreaded Python GIL (Global Interpreter Lock). Unfortunately when working with containers, multi-process worker models can be difficult to work with as containers generally expect to only have a single process. Specifically this means if one of the forked workers is hit by an OOM and killed, the main process will simply restart it without triggering the usual metrics in Kubernetes for OOM'd Pods. Similarly we have a different way to handle multi-process concurrency in Kubernetes, through a Deployment with many replicas. In the simplest version would could use multiple replicas each handling only one request at a time, but using a thread pool improves throughput by taking advantage of the fact that most web applications are blocked on I/O most of the time (usually waiting for a response from a database or another web service).

## Why Twisted?

Gunicorn itself does have a threadpool mode, however it's somewhat awkward to work with as it uses the `futures` ThreadPool implementation. Twisted's ThreadPool is more efficent. This also allows installing the Prometheus metrics as a native Twisted web handler so it will work even if the threadpool is exhausted, meaning your metrics keep working even during a system overload.
