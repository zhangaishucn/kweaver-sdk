"""SDK resource: conversations (agent-app service).

Actual backend endpoints (agent-app v1):
  - Chat:      POST /api/agent-app/v1/app/{app_key}/chat/completion
  - Debug:     POST /api/agent-app/v1/app/{app_key}/debug/completion
  - Terminate: POST /api/agent-app/v1/app/{app_key}/chat/termination
  - Resume:    POST /api/agent-app/v1/app/{app_key}/chat/resume
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator

from kweaver.types import Conversation, Message, MessageChunk, Reference

if TYPE_CHECKING:
    from kweaver._http import HttpClient


class ConversationsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self, agent_id: str, *, title: str | None = None
    ) -> Conversation:
        """Create a logical conversation handle (client-side).

        The actual backend does not have a separate "create conversation" API.
        Conversations are implicitly created on first message.  The real
        conversation_id is assigned by the backend in the first response.
        Pass the returned Conversation to send_message; the SDK will omit the
        conversation_id on the first call so the backend creates one.
        """
        return Conversation(
            id="",
            agent_id=agent_id,
            title=title,
            message_count=0,
            last_active=None,
        )

    def send_message(
        self,
        conversation_id: str,
        content: str,
        *,
        agent_id: str,
        agent_version: str = "latest",
        stream: bool = False,
        debug: bool = False,
        history: list[dict[str, str]] | None = None,
    ) -> Message | Iterator[MessageChunk]:
        """Send a message to an agent.

        Args:
            conversation_id: Conversation ID (from create()).
            content: The user query.
            agent_id: Agent ID (used as app_key in URL).
            agent_version: Agent version (default "latest").
            stream: Whether to stream the response.
            debug: Use debug/completion endpoint instead of chat/completion.
            history: Optional conversation history.
        """
        if debug:
            path = f"/api/agent-app/v1/app/{agent_id}/debug/completion"
            body: dict[str, Any] = {
                "agent_id": agent_id,
                "agent_version": agent_version,
                "input": {
                    "query": content,
                    "history": history or [],
                },
            }
        else:
            path = f"/api/agent-app/v1/app/{agent_id}/chat/completion"
            body = {
                "agent_id": agent_id,
                "agent_version": agent_version,
                "query": content,
                "conversation_id": conversation_id,
                "stream": stream,
                "inc_stream": False,
            }
            if history is not None:
                body["history"] = history

        # Remove empty conversation_id — backend treats absent as "new conversation"
        if not body.get("conversation_id"):
            body.pop("conversation_id", None)

        if not stream:
            data = self._http.post(path, json=body, timeout=120.0)
            return _parse_message(data)

        return self._stream_message(path, body)

    def _stream_message(
        self, path: str, body: dict[str, Any]
    ) -> Iterator[MessageChunk]:
        body["stream"] = True
        body["inc_stream"] = True
        for event in self._http.stream_post(path, json=body, timeout=120.0):
            refs = [Reference(**r) for r in event.get("references", [])]
            yield MessageChunk(
                delta=event.get("delta", event.get("answer", "")),
                finished=event.get("finished", False),
                references=refs,
            )

    def terminate(self, agent_id: str, conversation_id: str) -> None:
        """Terminate an ongoing conversation."""
        self._http.post(
            f"/api/agent-app/v1/app/{agent_id}/chat/termination",
            json={"conversation_id": conversation_id},
        )

    def delete(self, id: str, *, agent_id: str | None = None) -> None:
        """Delete / terminate a conversation.

        The backend doesn't have a dedicated delete API;
        this calls termination if agent_id is provided.
        """
        if agent_id:
            self.terminate(agent_id, id)

    # ── Kept for backwards compat but may not be supported by backend ──

    def list(
        self, *, agent_id: str | None = None, limit: int | None = None
    ) -> list[Conversation]:
        """List conversations. Note: may not be available in all deployments."""
        return []

    def get(self, id: str) -> Conversation:
        """Get conversation by ID. Note: may not be available in all deployments."""
        return Conversation(id=id, agent_id="")

    def list_messages(
        self,
        conversation_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Message]:
        """List messages. Note: may not be available in all deployments."""
        return []


def _parse_conversation(d: Any) -> Conversation:
    return Conversation(
        id=str(d.get("id", d.get("conversation_id", ""))),
        agent_id=d.get("agent_id", ""),
        title=d.get("title"),
        message_count=d.get("message_count", 0),
        last_active=d.get("last_active"),
    )


def _parse_message(d: Any) -> Message:
    refs = [Reference(**r) for r in (d.get("references") or [])]
    # agent-app response format: answer field contains the reply
    content = d.get("content") or d.get("answer") or ""
    msg_id = d.get("id") or d.get("message_id") or d.get("assistant_message_id") or ""
    return Message(
        id=str(msg_id),
        role=d.get("role", "assistant"),
        content=content,
        references=refs,
        timestamp=d.get("timestamp") or d.get("created_at") or "",
    )
