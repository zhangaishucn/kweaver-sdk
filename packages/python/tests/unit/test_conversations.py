"""Tests for conversations resource (agent-app v1 API)."""

from unittest.mock import patch

import httpx

from tests.conftest import RequestCapture, make_client


def test_create_conversation():
    """Create returns a client-side conversation handle (no backend call)."""
    client = make_client(lambda r: httpx.Response(200, json={}))
    conv = client.conversations.create("agent_01", title="测试会话")
    assert conv.id == ""  # Placeholder; backend assigns ID on first message
    assert conv.agent_id == "agent_01"
    assert conv.title == "测试会话"


def test_send_message_sync(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "message_id": "msg_02", "role": "assistant",
            "answer": "物料库存充足",
            "references": [
                {"source": "库存表", "content": "华东仓 1200件", "score": 0.95},
            ],
            "created_at": "2026-03-12T10:01:00Z",
        })

    client = make_client(handler, capture)
    reply = client.conversations.send_message(
        "conv_01", "库存情况？", agent_id="agent_01",
    )
    assert reply.role == "assistant"
    assert reply.content == "物料库存充足"
    assert len(reply.references) == 1
    assert reply.references[0].source == "库存表"
    body = capture.last_body()
    assert body["query"] == "库存情况？"
    assert body["agent_id"] == "agent_01"
    assert "/app/agent_01/chat/completion" in capture.last_url()


def test_send_message_debug(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "message_id": "msg_03", "answer": "调试回复",
        })

    client = make_client(handler, capture)
    reply = client.conversations.send_message(
        "conv_01", "测试问题", agent_id="agent_01", debug=True,
    )
    assert reply.content == "调试回复"
    assert "/app/agent_01/debug/completion" in capture.last_url()
    body = capture.last_body()
    assert body["input"]["query"] == "测试问题"


def test_send_message_stream():
    chunks = [
        {"delta": "物料", "finished": False, "references": []},
        {"delta": "库存充足", "finished": True,
         "references": [{"source": "库存表", "content": "1200件", "score": 0.9}]},
    ]
    client = make_client(lambda r: httpx.Response(200, json={}))
    with patch.object(
        client.conversations._http, "stream_post", return_value=iter(chunks)
    ):
        result = list(
            client.conversations.send_message(
                "conv_01", "hi", agent_id="agent_01", stream=True,
            )
        )
    assert len(result) == 2
    assert result[0].delta == "物料"
    assert not result[0].finished
    assert result[1].delta == "库存充足"
    assert result[1].finished
    assert result[1].references[0].source == "库存表"


def test_terminate_conversation(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    client = make_client(handler, capture)
    client.conversations.terminate("agent_01", "conv_01")
    assert "/app/agent_01/chat/termination" in capture.last_url()


def test_delete_calls_terminate(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    client = make_client(handler, capture)
    client.conversations.delete("conv_01", agent_id="agent_01")
    assert "/chat/termination" in capture.last_url()
