"""SDK resource: agents (agent-factory service).

Actual backend endpoints (agent-factory v3):
  - List:   POST /api/agent-factory/v3/published/agent
  - Detail: GET  /api/agent-factory/v3/agent/{id}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kweaver.types import Agent

if TYPE_CHECKING:
    from kweaver._http import HttpClient


class AgentsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Agent]:
        """List published agents.

        Args:
            keyword: Filter by name substring.
            status: Ignored (kept for API compatibility). The published
                    endpoint only returns published agents.
            offset: Pagination offset (default 0).
            limit: Max items to return (default 50).
        """
        body: dict[str, Any] = {
            "offset": offset,
            "limit": limit,
            "name": keyword or "",
            "category_id": "",
            "custom_space_id": "",
            "is_to_square": 1,
        }

        # The agent-factory API requires text/plain content-type for this
        # endpoint (application/json returns empty results — platform quirk).
        data = self._http.post(
            "/api/agent-factory/v3/published/agent",
            json=body,
            headers={"content-type": "text/plain;charset=UTF-8"},
        )
        items = (
            data
            if isinstance(data, list)
            else (data.get("entries") or data.get("data") or [])
        )
        return [_parse_agent(d) for d in items]

    def get(self, id: str) -> Agent:
        data = self._http.get(f"/api/agent-factory/v3/agent/{id}")
        return _parse_agent(data)


def _parse_agent(d: Any) -> Agent:
    # Extract knowledge network IDs from config.data_source.kg
    kn_ids: list[str] = d.get("kn_ids", [])
    config = d.get("config") or {}
    if not kn_ids:
        ds = config.get("data_source") or {}
        kn_ids = [kg["kg_id"] for kg in (ds.get("kg") or []) if kg.get("kg_id")]
        kn_entry = (ds.get("kn_entry") or ds.get("knowledge_network")) or {}
        if isinstance(kn_entry, list):
            kn_ids.extend(e.get("id", "") for e in kn_entry if e.get("id"))

    # Map agent-factory status to simplified status
    raw_status = d.get("status", "unpublished")
    if raw_status in ("published", "published_edited"):
        status = "published"
    else:
        status = "draft"

    return Agent(
        id=str(d.get("id", "")),
        name=d.get("name", ""),
        key=d.get("key"),
        version=d.get("version"),
        description=d.get("profile") or d.get("description"),
        status=status,
        kn_ids=kn_ids,
        system_prompt=config.get("system_prompt") or d.get("system_prompt"),
        capabilities=d.get("capabilities", []),
        model_config_data=config.get("llms") or d.get("model_config"),
        conversation_count=d.get("conversation_count", 0),
    )
