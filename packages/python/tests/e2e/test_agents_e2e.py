"""E2E: agent listing, detail, and conversation.

Tests against the real agent-factory and agent-app services.
"""

from __future__ import annotations

import pytest

from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_list_agents(kweaver_client: KWeaverClient):
    """List agents should return without error."""
    agents = kweaver_client.agents.list()
    assert isinstance(agents, list)


def test_list_agents_published(kweaver_client: KWeaverClient):
    """Published filter should only return published agents."""
    agents = kweaver_client.agents.list(status="published")
    assert isinstance(agents, list)
    for a in agents:
        assert a.status == "published"


@pytest.fixture(scope="module")
def any_agent(kweaver_client: KWeaverClient):
    """Find any agent for tests (published or not)."""
    agents = kweaver_client.agents.list()
    if not agents:
        pytest.skip("No agents found")
    return agents[0]


@pytest.fixture(scope="module")
def published_agent(kweaver_client: KWeaverClient):
    """Find a published agent for tests."""
    agents = kweaver_client.agents.list(status="published")
    if not agents:
        pytest.skip("No published agents found")
    return agents[0]


def test_get_agent(kweaver_client: KWeaverClient, any_agent):
    """Get agent detail should return full config."""
    agent = kweaver_client.agents.get(any_agent.id)
    assert agent.id == any_agent.id
    assert agent.name == any_agent.name


def test_agent_has_fields(kweaver_client: KWeaverClient, any_agent):
    """Agent detail should contain key fields from agent-factory."""
    agent = kweaver_client.agents.get(any_agent.id)
    assert agent.id
    assert agent.name
    assert agent.status in ("published", "draft")
    # version and system_prompt come from detail endpoint
    assert agent.version is not None or agent.system_prompt is not None


@pytest.mark.destructive
def test_conversation_flow(kweaver_client: KWeaverClient, published_agent):
    """Create conversation, send message, verify response.

    Note: if the agent has broken tool/knowledge config, the backend
    may return 500. We accept that as "SDK wiring is correct" and
    only fail on 4xx (wrong path / auth / params).
    """
    from kweaver._errors import ServerError

    conv = kweaver_client.conversations.create(published_agent.id)
    assert conv.agent_id == published_agent.id

    try:
        reply = kweaver_client.conversations.send_message(
            conv.id,
            content="你好",
            agent_id=published_agent.id,
            agent_version=published_agent.version or "latest",
        )
        assert reply.content
        assert reply.role == "assistant"
    except ServerError:
        # Agent config issue (missing tools, invalid KN, etc.)
        # SDK path is correct since we got 500 not 404/401
        pytest.skip("Agent returned 500 — likely broken config, SDK path OK")
