"""VegaTasksResource — discover and metric task operations."""
from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

from kweaver.types import VegaDiscoverTask, VegaMetricTask

if TYPE_CHECKING:
    from kweaver._http import HttpClient

_DISCOVER_BASE = "/api/vega-backend/v1/discover-tasks"
_METRIC_BASE = "/api/mdl-data-model/v1/metric-tasks"

_TERMINAL = {"completed", "failed"}


class VegaTasksResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list_discover(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[VegaDiscoverTask]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status is not None:
            params["status"] = status
        data = self._http.get(_DISCOVER_BASE, params=params)
        entries = (
            data.get("entries", data.get("data", [])) if isinstance(data, dict) else data
        )
        return [VegaDiscoverTask(**e) for e in entries]

    def get_discover(self, id: str) -> VegaDiscoverTask:
        data = self._http.get(f"{_DISCOVER_BASE}/{id}")
        if isinstance(data, dict) and "entries" in data:
            data = data["entries"][0] if data["entries"] else data
        return VegaDiscoverTask(**data)

    def wait_discover(
        self,
        id: str,
        *,
        timeout: float = 300,
        interval: float = 2.0,
    ) -> VegaDiscoverTask:
        """Poll get_discover() until terminal state with exponential backoff (max 30s)."""
        deadline = time.time() + timeout
        current_interval = interval
        while True:
            task = self.get_discover(id)
            if task.status in _TERMINAL:
                return task
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(
                    f"Discover task {id!r} did not reach terminal state within {timeout}s"
                )
            sleep_time = min(current_interval, remaining, 30.0)
            time.sleep(sleep_time)
            current_interval = min(current_interval * 2, 30.0)

    def get_metric(self, task_id: str) -> VegaMetricTask:
        data = self._http.get(f"{_METRIC_BASE}/{task_id}")
        if isinstance(data, dict) and "entries" in data:
            data = data["entries"][0] if data["entries"] else data
        return VegaMetricTask(**data)
