"""VegaConnectorTypesResource — connector type listing and detail."""
from __future__ import annotations
from typing import TYPE_CHECKING
from kweaver.types import VegaConnectorType

if TYPE_CHECKING:
    from kweaver._http import HttpClient


class VegaConnectorTypesResource:
    _BASE = "/api/vega-backend/v1/connector-types"

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> list[VegaConnectorType]:
        data = self._http.get(self._BASE)
        entries = data.get("entries", data.get("data", [])) if isinstance(data, dict) else data
        return [VegaConnectorType(**e) for e in entries]

    def get(self, type: str) -> VegaConnectorType:
        data = self._http.get(f"{self._BASE}/{type}")
        if isinstance(data, dict) and "entries" in data:
            data = data["entries"][0] if data["entries"] else data
        return VegaConnectorType(**data)
