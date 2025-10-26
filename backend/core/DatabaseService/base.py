from __future__ import annotations
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, Generic, List, Optional, Sequence, Tuple, Type, \
    TypeVar, Union
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.exc import DBAPIError, OperationalError, InterfaceError
from asyncpg.exceptions import PostgresError
from sqlmodel import SQLModel, select, and_
from ..LoggingService import logger
from backend.core.config import get_settings
from sqlalchemy.orm import sessionmaker
from dataclasses import dataclass
from sqlalchemy import text
from time import time
import contextlib

try:
    # Sizning mavjud professional logger xizmatingiz
    logger.info(f"✅ LoggerService initialized for DB module in {get_settings().APP_ENV} mode.")
    APP_NAME = "DatabaseService"

except Exception as e:
    # Minimal fallback (agar log moduli topilmasa ham ishlaydi)
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("core.db")
    logger.warning(f"⚠️ LoggerService fallback ishlatildi: {e}")
    APP_NAME = "DatabaseService"

T = TypeVar("T", bound=SQLModel)


@dataclass(frozen=True)
class EngineConfig:
    url: str
    echo: bool = False
    pool_size: int = 50
    max_overflow: int = 25
    pool_timeout: int = 30
    pool_recycle: int = 1800  # 30 min
    statement_timeout_ms: int = 60_000
    idle_tx_timeout_ms: int = 300_000
    application_name: str = APP_NAME


class _EngineSingleton:
    """Thread-safe emas, ammo process-local bo'lgani uchun FastAPI kontekstida yetarli."""
    _engine: Optional[AsyncEngine] = None

    @classmethod
    def get_engine(cls, cfg: EngineConfig) -> AsyncEngine:
        if cls._engine is None:
            logger.info("Initializing AsyncEngine for PostgreSQL...")
            cls._engine = create_async_engine(
                cfg.url,
                echo=cfg.echo,
                pool_size=cfg.pool_size,
                max_overflow=cfg.max_overflow,
                pool_timeout=cfg.pool_timeout,
                pool_recycle=cfg.pool_recycle,
                pool_pre_ping=True,
                connect_args={
                    "server_settings": {
                        "application_name": cfg.application_name,
                        "statement_timeout": str(cfg.statement_timeout_ms),
                        "idle_in_transaction_session_timeout": str(cfg.idle_tx_timeout_ms),
                    }
                },
            )
        return cls._engine


class SessionProvider:
    """AsyncSession factory (expire_on_commit=False — SQLModel/ORM obyektlarini qayta ishlatish uchun qulay)."""

    def __init__(self, engine: AsyncEngine):
        self._session_factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    def get(self) -> AsyncSession:
        return self._session_factory()


class DatabaseError(Exception):
    """DB umumiy Exception sathi — kerak bo‘lsa kengaytiring."""


class DatabaseService:
    """
    Industrial darajadagi, asinxron, retry qo'llovchi va toza Session boshqaruv xizmati.
    — session_scope(): commit/rollback/close ni toza tutadi
    — execute(): har qanday async query/callable ni retry bilan bajaradi
    — add/get/update/update_by_field: ko‘p hollik CRUD qisqa yo‘llari
    """
    MAX_RETRIES = 5

    def __init__(self, engine: Optional[AsyncEngine] = None, cfg: Optional[EngineConfig] = None):
        cfg = cfg or EngineConfig(url=get_settings().DATABASE_URL)
        self.engine: AsyncEngine = engine or _EngineSingleton.get_engine(cfg)
        self.sessions = SessionProvider(self.engine)
        self._log = logger

    @contextlib.asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        session = self.sessions.get()
        try:
            yield session
            await session.commit()
        except (DBAPIError, OperationalError, InterfaceError, PostgresError) as db_err:
            self._log.error("Database error during session_scope", exc_info=True)
            await session.rollback()
            raise
        except Exception:
            self._log.error("General error during session_scope", exc_info=True)
            await session.rollback()
            raise
        finally:
            with contextlib.suppress(Exception):
                await session.close()

    def get_session(self) -> AsyncSession:
        return self.sessions.get()

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(MAX_RETRIES),
        retry=retry_if_exception_type((DBAPIError, OperationalError, InterfaceError, PostgresError)),
        reraise=True,
    )
    async def execute(self, fn: Callable[[AsyncSession], Awaitable[Any]], *, label: Optional[str] = None) -> Any:
        start = time()
        async with self.session_scope() as session:
            try:
                if label:
                    self._log.info(f"[DB] Executing: {label}")
                res = await fn(session)
                took = time() - start
                self._log.info(f"[DB] Done in {took:.2f}s")
                return res
            except (DBAPIError, OperationalError, InterfaceError, PostgresError):
                self._log.error("[DB] DB-level failure in execute()", exc_info=True)
                raise
            except Exception:
                self._log.error("[DB] General failure in execute()", exc_info=True)
                raise

    # ---------- CRUD SHORTCUTS ----------

    async def add(self, instance: T) -> Optional[Any]:
        """Yangi yozuv qo‘shadi. Agar instance.id mavjud bo‘lsa, DB autogeneratoriga yo‘l berish uchun None ga tenglashtirmaydi — UUID/PK siyosatingizga mos ravishda qoldiriladi."""
        async with self.session_scope() as session:
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            self._log.info(f"[DB] Added: {instance.__class__.__name__}({getattr(instance, 'id', None)})")
            return getattr(instance, "id", None)

    async def list(
            self,
            model: Type[T],
            filters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            order_by: Optional[Sequence[Any]] = None,
    ) -> List[T]:
        """Oddiy tenglikka asoslangan filtrlash (kengaytirilgan operatorlar uchun repositories.py dagi BaseRepository'dan foydalaning)."""
        async with self.session_scope() as session:
            query = select(model)
            conditions: List[Any] = []
            if filters:
                for k, v in filters.items():
                    if hasattr(model, k):
                        conditions.append(getattr(model, k) == v)
            if conditions:
                query = query.where(and_(*conditions))
            if order_by:
                query = query.order_by(*order_by)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            res = await session.execute(query)
            return list(res.scalars().all())

    async def update(self, instance: T) -> Optional[Any]:
        async with self.session_scope() as session:
            merged = await session.merge(instance)
            await session.flush()
            await session.refresh(merged)
            self._log.info(f"[DB] Updated: {instance.__class__.__name__}({getattr(merged, 'id', None)})")
            return getattr(merged, "id", None)

    async def update_by_field(
            self,
            model: Type[T],
            field_name: str,
            field_value: Any,
            updates: Dict[str, Any],
    ) -> Optional[Any]:
        async with self.session_scope() as session:
            if not hasattr(model, field_name):
                raise AttributeError(f"{model.__name__} has no field '{field_name}'")
            stmt = select(model).where(getattr(model, field_name) == field_value)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            if not instance:
                self._log.warning(f"[DB] {model.__name__} where {field_name}={field_value} not found")
                return None
            for k, v in updates.items():
                if v is not None and hasattr(instance, k):
                    setattr(instance, k, v)
            merged = await session.merge(instance)
            await session.flush()
            await session.refresh(merged)
            return getattr(merged, "id", None)

    # ---------- Health / Diagnostics ----------

    async def ping(self) -> bool:
        """DB sog'ligini tekshiradi (1=ok, 0=fail)."""
        try:
            async with self.session_scope() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            self._log.error("[DB] ping() failed", exc_info=True)
            return False

    async def one_or_none(self, stmt) -> Any:
        """
        Executes a SELECT statement and returns a single result or None.
        Ideal for unique lookups (e.g., by ID, unique constraint).
        """

        async def _fetch(session: AsyncSession):
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self.execute(_fetch, label="one_or_none")

    async def soft_delete_many(
            self,
            model: Type[T],
            filters: Dict[str, Any]
    ) -> int:
        """
        Soft delete (is_deleted=True) ni filter asosida ko‘p yozuvlarga qo‘llaydi.
        Faqat 'is_deleted' maydoni mavjud bo‘lgan modellarda ishlaydi.
        """
        async with self.session_scope() as session:
            if not hasattr(model, "is_deleted"):
                raise AttributeError(f"{model.__name__} does not have 'is_deleted' field.")

            stmt = select(model)
            conditions = [getattr(model, k) == v for k, v in filters.items() if hasattr(model, k)]
            if not conditions:
                self._log.warning(f"[DB] No valid filters provided for {model.__name__}. Aborting soft delete.")
                return 0

            stmt = stmt.where(and_(*conditions))
            result = await session.execute(stmt)
            instances = result.scalars().all()

            for instance in instances:
                setattr(instance, "is_deleted", True)
                session.add(instance)

            self._log.info(f"[DB] Soft-deleted {len(instances)} {model.__name__} record(s).")
            return len(instances)

    async def delete_many(
            self,
            model: Type[T],
            filters: Dict[str, Any],
    ) -> int:
        """
        Berilgan filterlar asosida ko‘p yozuvlarni to‘liq o‘chiradi (DELETE FROM ...).
        Faqat ehtiyotkorlik bilan ishlatish tavsiya etiladi.
        """
        async with self.session_scope() as session:
            if not filters:
                self._log.warning(
                    f"[DB] delete_many() called without filters for {model.__name__}. Aborting to prevent full-table delete.")
                return 0

            # Shartlarni yig‘ish
            conditions = [getattr(model, k) == v for k, v in filters.items() if hasattr(model, k)]
            if not conditions:
                self._log.warning(f"[DB] delete_many() no valid conditions found for {model.__name__}.")
                return 0

            stmt = select(model).where(and_(*conditions))
            result = await session.execute(stmt)
            instances = result.scalars().all()

            if not instances:
                self._log.info(f"[DB] No records found for delete_many() on {model.__name__} with {filters}.")
                return 0

            # O‘chirish
            for instance in instances:
                await session.delete(instance)

            count = len(instances)
            self._log.info(f"[DB] Deleted {count} record(s) from {model.__name__} matching {filters}.")
            return count


# FastAPI dependency
async def get_db() -> DatabaseService:
    return DatabaseService()
