from __future__ import annotations
from typing import Any, Dict, List, Sequence, Tuple, Type
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import asc, desc
from sqlalchemy import text, or_
from sqlmodel import SQLModel


# -------- Health Check --------

async def health_check(engine: AsyncEngine) -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


# -------- Filter Builder --------
# qo'llab-quvvatlanadigan operatorlar: eq, ne, gt, gte, lt, lte, like, ilike, in, nin, contains, overlap
# sintaksis: {"age__gte": 18, "name__ilike": "%ali%", "status__in": ["ACTIVE","PENDING"]}

def build_filters(model: Type[SQLModel], filters: Dict[str, Any]) -> List[Any]:
    conds: List[Any] = []
    for raw_key, value in filters.items():
        if "__" in raw_key:
            field_name, op = raw_key.split("__", 1)
        else:
            field_name, op = raw_key, "eq"

        if not hasattr(model, field_name):
            continue

        column = getattr(model, field_name)

        if op == "eq":
            conds.append(column == value)
        elif op == "ne":
            conds.append(column != value)
        elif op in ("gt", "gte", "lt", "lte"):
            if op == "gt":
                conds.append(column > value)
            elif op == "gte":
                conds.append(column >= value)
            elif op == "lt":
                conds.append(column < value)
            elif op == "lte":
                conds.append(column <= value)
        elif op == "like":
            conds.append(column.like(value))
        elif op == "ilike":
            conds.append(column.ilike(value))
        elif op == "in":
            if isinstance(value, (list, tuple, set)):
                conds.append(column.in_(list(value)))
        elif op == "nin":
            if isinstance(value, (list, tuple, set)):
                conds.append(~column.in_(list(value)))
        elif op == "contains":
            # JSON/ARRAY ustunlar uchun
            try:
                conds.append(column.contains(value))
            except Exception:
                # ba'zi DB dialektlarida mavjud bo'lmasligi mumkin
                pass
        elif op == "overlap":
            # ARRAY overlap
            try:
                conds.append(column.overlap(value))
            except Exception:
                pass
        else:
            # noma'lum operatorni e'tiborsiz qoldiramiz (yoki Exception ko'tarish mumkin)
            continue

    return conds


# -------- Order Builder --------
# order: ["-created_at", "name"]  ⇒ minus DESC, boshqa holatda ASC

def build_order_by(model: Type[SQLModel], order: Sequence[str]) -> List[Any]:
    clauses: List[Any] = []
    for key in order:
        direction = asc
        field_name = key
        if key.startswith("-"):
            direction = desc
            field_name = key[1:]
        if hasattr(model, field_name):
            clauses.append(direction(getattr(model, field_name)))
    return clauses
