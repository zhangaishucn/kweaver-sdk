"""VegaQueryResource -- query execution and DSL search."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kweaver.types import VegaDslResult, VegaPromqlResult, VegaQueryResult

if TYPE_CHECKING:
    from kweaver._http import HttpClient


class VegaQueryResource:
    def __init__(self, http: "HttpClient") -> None:
        self._http = http

    def execute(
        self,
        *,
        tables: list[str] | None = None,
        filter_condition: Any = None,
        output_fields: list[str] | None = None,
        sort: list[dict[str, Any]] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> VegaQueryResult:
        body: dict[str, Any] = {}
        if tables:
            body["tables"] = tables
        if filter_condition:
            body["filter_condition"] = filter_condition
        if output_fields:
            body["output_fields"] = output_fields
        if sort:
            body["sort"] = sort
        body["offset"] = offset
        body["limit"] = limit
        data = self._http.post("/api/vega-backend/v1/query/execute", json=body)
        return VegaQueryResult(**data) if data else VegaQueryResult()

    def dsl(self, *, index: str | None = None, body: dict) -> VegaDslResult:
        path = (
            f"/api/mdl-uniquery/v1/dsl/{index}/_search"
            if index
            else "/api/mdl-uniquery/v1/dsl/_search"
        )
        data = self._http.post(path, json=body)
        return VegaDslResult(**data) if data else VegaDslResult()

    def dsl_count(self, *, index: str | None = None, body: dict) -> int:
        path = (
            f"/api/mdl-uniquery/v1/dsl/{index}/_count"
            if index
            else "/api/mdl-uniquery/v1/dsl/_count"
        )
        data = self._http.post(path, json=body)
        return data.get("count", 0) if data else 0

    def promql(
        self, *, query: str, start: str, end: str, step: str
    ) -> VegaPromqlResult:
        data = self._http.post(
            "/api/mdl-uniquery/v1/promql/query_range",
            json={"query": query, "start": start, "end": end, "step": step},
        )
        return VegaPromqlResult(**data.get("data", data)) if data else VegaPromqlResult()

    def promql_instant(self, *, query: str) -> VegaPromqlResult:
        data = self._http.post(
            "/api/mdl-uniquery/v1/promql/query",
            json={"query": query},
        )
        return VegaPromqlResult(**data.get("data", data)) if data else VegaPromqlResult()

    def events(self, *, body: dict) -> VegaDslResult:
        data = self._http.post("/api/mdl-uniquery/v1/events", json=body)
        return VegaDslResult(**data) if data else VegaDslResult()
