from typing import Iterable

from prometheus_client.core import GaugeMetricFamily, Metric  # type: ignore


class TwistedThreadPoolCollector:
    def __init__(self, pool):
        self.pool = pool

    def collect(self) -> Iterable[Metric]:
        stats = self.pool._team.statistics()
        yield GaugeMetricFamily(
            "twisted_threadpool_idle_worker_count",
            "The number of idle workers.",
            value=stats.idleWorkerCount,
        )
        yield GaugeMetricFamily(
            "twisted_threadpool_busy_worker_count",
            "The number of busy workers.",
            value=stats.busyWorkerCount,
        )
        yield GaugeMetricFamily(
            "twisted_threadpool_backlogged_work_count",
            """The number of work items passed to Team.do
which have not yet been sent to a worker to be performed because not
enough workers are available.""",
            value=stats.backloggedWorkCount,
        )
