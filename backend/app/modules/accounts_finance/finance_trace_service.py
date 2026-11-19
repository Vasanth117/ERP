"""Register and traverse finance transaction relationships."""

import uuid

from beanie.odm.operators.find.comparison import Eq

from app.modules.accounts_finance.phase12_models import FinanceTransactionRelationship


async def register_finance_relationship(
    tenant_id,
    *,
    link_type: str,
    from_type: str,
    from_id: str,
    to_type: str,
    to_id: str,
    metadata: dict | None = None,
) -> str:
    existing = await FinanceTransactionRelationship.find_one(
        Eq(FinanceTransactionRelationship.tenant_id, tenant_id),
        Eq(FinanceTransactionRelationship.link_type, link_type),
        Eq(FinanceTransactionRelationship.from_id, from_id),
        Eq(FinanceTransactionRelationship.to_id, to_id),
    )
    if existing:
        return existing.relationship_id
    relationship_id = f"fxr_{uuid.uuid4().hex[:10]}"
    await FinanceTransactionRelationship(
        tenant_id=tenant_id,
        relationship_id=relationship_id,
        link_type=link_type,
        from_type=from_type,
        from_id=from_id,
        to_type=to_type,
        to_id=to_id,
        metadata=metadata or {},
    ).insert()
    return relationship_id


async def trace_from_root(tenant_id, root_type: str, root_id: str) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    edges: list[dict] = []
    queue = [(root_type, root_id)]
    while queue:
        node_type, node_id = queue.pop(0)
        if (node_type, node_id) in seen:
            continue
        seen.add((node_type, node_id))
        forwards = await FinanceTransactionRelationship.find(
            Eq(FinanceTransactionRelationship.tenant_id, tenant_id),
            Eq(FinanceTransactionRelationship.from_type, node_type),
            Eq(FinanceTransactionRelationship.from_id, node_id),
        ).to_list()
        backwards = await FinanceTransactionRelationship.find(
            Eq(FinanceTransactionRelationship.tenant_id, tenant_id),
            Eq(FinanceTransactionRelationship.to_type, node_type),
            Eq(FinanceTransactionRelationship.to_id, node_id),
        ).to_list()
        for rel in forwards + backwards:
            edges.append(rel.model_dump())
            queue.append((rel.to_type, rel.to_id))
            queue.append((rel.from_type, rel.from_id))
    return edges