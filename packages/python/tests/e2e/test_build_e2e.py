"""E2E: knowledge network build flow (datasource → dataview → KN → build).

These tests create and delete knowledge networks, so they are marked as
destructive and require ``--run-destructive`` to run.
"""

from __future__ import annotations

from typing import Any

import pytest

from kweaver import KWeaverClient

pytestmark = [pytest.mark.e2e, pytest.mark.destructive]


def test_dataview_create_from_table(
    create_datasource, kweaver_client: KWeaverClient,
):
    """Find the auto-created atomic dataview for a real table."""
    ds = create_datasource(name="e2e_dv_test")
    tables = kweaver_client.datasources.list_tables(ds.id)
    assert len(tables) > 0

    dv = kweaver_client.dataviews.create(
        name=f"e2e_dv_{tables[0].name}",
        datasource_id=ds.id,
        table=tables[0].name,
        columns=tables[0].columns,
    )
    assert dv.id
    assert dv.name


def test_build_knowledge_network(
    create_datasource,
    create_knowledge_network,
    kweaver_client: KWeaverClient,
):
    """Full build: datasource → dataview → KN → object type."""
    # 1. Datasource and table discovery
    ds = create_datasource(name="e2e_build_test")
    tables = kweaver_client.datasources.list_tables(ds.id)
    assert len(tables) > 0
    table = tables[0]

    # 2. Create dataview
    dv = kweaver_client.dataviews.create(
        name=f"e2e_build_{table.name}",
        datasource_id=ds.id,
        table=table.name,
        columns=table.columns,
    )
    assert dv.id

    # 3. Create knowledge network
    kn = create_knowledge_network(name="e2e_build_kn")
    assert kn.id

    # 4. Create object type — pick first suitable column as PK
    pk_col = table.columns[0].name
    ot = kweaver_client.object_types.create(
        kn.id,
        name=f"e2e_{table.name}",
        dataview_id=dv.id,
        primary_keys=[pk_col],
        display_key=pk_col,
    )
    assert ot.id


def test_build_with_relation(
    create_datasource,
    create_knowledge_network,
    kweaver_client: KWeaverClient,
):
    """Build with two tables and a relation between them."""
    ds = create_datasource(name="e2e_rel_test")
    tables = kweaver_client.datasources.list_tables(ds.id)
    if len(tables) < 2:
        pytest.skip("Need at least 2 tables for relation test")

    t1, t2 = tables[0], tables[1]
    dv1 = kweaver_client.dataviews.create(name=f"e2e_rel_{t1.name}", datasource_id=ds.id, table=t1.name, columns=t1.columns)
    dv2 = kweaver_client.dataviews.create(name=f"e2e_rel_{t2.name}", datasource_id=ds.id, table=t2.name, columns=t2.columns)

    kn = create_knowledge_network(name="e2e_rel_kn")

    ot1 = kweaver_client.object_types.create(
        kn.id, name=f"e2e_{t1.name}", dataview_id=dv1.id,
        primary_keys=[t1.columns[0].name], display_key=t1.columns[0].name,
    )
    ot2 = kweaver_client.object_types.create(
        kn.id, name=f"e2e_{t2.name}", dataview_id=dv2.id,
        primary_keys=[t2.columns[0].name], display_key=t2.columns[0].name,
    )
    assert ot1.id
    assert ot2.id

    # Create a direct relation using first column of each
    rt = kweaver_client.relation_types.create(
        kn.id,
        name=f"e2e_{t1.name}_{t2.name}",
        source_ot_id=ot1.id,
        target_ot_id=ot2.id,
        mappings=[(t1.columns[0].name, t2.columns[0].name)],
    )
    assert rt.id
