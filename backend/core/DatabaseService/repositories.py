from __future__ import annotations
from typing import Any, Dict, Generic, Iterable, List, Optional, Sequence, Type, TypeVar
from sqlmodel import SQLModel, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from .base import DatabaseService
from .utils import build_filters, build_order_by
from sqlalchemy import func


T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """
    Domain repositorylar uchun poydevor.
    — Kengaytirilgan filtr operatorlari: eq, ne, gt, gte, lt, lte, like, ilike, in, nin, contains, overlap
      Sintaksis: {"age__gte": 18, "name__ilike": "%ali%", "status__in": ["ACTIVE","PENDING"]}
    — Pagination: limit/offset
    — Ordering: ["-created_at", "name"]  ⇒ minus = DESC
    """

    def __init__(self, model: Type[T], db: Optional[DatabaseService] = None):
        self.model = model
        self.db = db or DatabaseService()

    async def get_session(self) -> AsyncSession:
        return self.db.get_session()

    async def get_by_id(self, id_value: Any) -> Optional[T]:
        async with self.db.session_scope() as session:
            stmt = select(self.model).where(self.model.id == id_value)
            res = await session.execute(stmt)
            return res.scalar_one_or_none()

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[Sequence[str]] = None,
        or_filters: Optional[List[Dict[str, Any]]] = None,
    ) -> List[T]:
        """Kengaytirilgan filter + OR kombinatsiyalarini qo‘llab-quvvatlaydi."""
        async with self.db.session_scope() as session:
            stmt = select(self.model)

            # AND blok
            and_conds = build_filters(self.model, filters or {})
            if and_conds:
                stmt = stmt.where(and_(*and_conds))

            # OR blok: ro'yxatdagi har bir dict bitta OR sharti sifatida ko'riladi
            if or_filters:
                or_blocks = []
                for f in or_filters:
                    conds = build_filters(self.model, f)
                    if conds:
                        or_blocks.append(and_(*conds))
                if or_blocks:
                    stmt = stmt.where(or_(*or_blocks))

            if order:
                stmt = stmt.order_by(*build_order_by(self.model, order))
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())

    async def create(self, instance: T) -> T:
        async with self.db.session_scope() as session:
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance

    async def bulk_create(self, instances: Iterable[T]) -> List[T]:
        async with self.db.session_scope() as session:
            session.add_all(list(instances))
            await session.flush()
            # refresh_all yo'q; kerakli bo'lsa alohida qayta yuklang
            return list(instances)

    async def update(self, instance: T) -> T:
        async with self.db.session_scope() as session:
            merged = await session.merge(instance)
            await session.flush()
            await session.refresh(merged)
            return merged

    async def update_fields(self, id_value: Any, updates: Dict[str, Any]) -> Optional[T]:
        async with self.db.session_scope() as session:
            stmt = select(self.model).where(self.model.id == id_value)
            res = await session.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                return None
            for k, v in updates.items():
                if v is not None and hasattr(obj, k):
                    setattr(obj, k, v)
            merged = await session.merge(obj)
            await session.flush()
            await session.refresh(merged)
            return merged

    async def delete_soft(self, id_value: Any) -> bool:
        """Soft-delete (is_deleted=True) mavjud bo'lsa, modelda shu maydon ishlaydi."""
        async with self.db.session_scope() as session:
            stmt = select(self.model).where(self.model.id == id_value)
            res = await session.execute(stmt)
            obj = res.scalar_one_or_none()
            if not obj:
                return False
            if hasattr(obj, "is_deleted"):
                setattr(obj, "is_deleted", True)
                await session.merge(obj)
                return True
            # Agar soft-delete yo'q bo'lsa, hard-delete qilamiz:
            await session.delete(obj)
            return True

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        async with self.db.session_scope() as session:
            stmt = select(func.count()).select_from(self.model)
            conds = build_filters(self.model, filters or {})
            if conds:
                stmt = stmt.where(and_(*conds))
            res = await session.execute(stmt)
            return int(res.scalar() or 0)
