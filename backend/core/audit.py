from __future__ import annotations
from typing import Callable, Awaitable, Optional, Any, Dict
from functools import wraps
import inspect

from backend.core.LoggingService import logger
from backend.core.middleware.request_context import get_request_context
from backend.domain.audit.services import AuditService


def _extract_entity_id(result: Any, entity_id_key: Optional[str]) -> Optional[str]:
    """
    Result obyektidan entity_id ni topish (id/uuid maydoni yoki dict key).
    """
    if entity_id_key is None or result is None:
        return None
    # SQLModel or dataclass with attribute:
    if hasattr(result, entity_id_key):
        return str(getattr(result, entity_id_key))
    # Dict-like:
    if isinstance(result, dict) and entity_id_key in result:
        return str(result[entity_id_key])
    # Fallback: try 'id'
    if hasattr(result, "id"):
        return str(getattr(result, "id"))
    return None


def audit_action(
    *,
    action: str,
    entity_type: Optional[str] = None,
    entity_id_key: Optional[str] = "id",   # natijadan id olishga urinamiz
):
    """
    Usage:
        @audit_action(action="ORG.UNIT.CREATE", entity_type="OrgUnit")
        async def create_unit(...): ...
    """
    def decorator(fn: Callable[..., Awaitable[Any]]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            ctx = get_request_context()
            svc = AuditService()
            try:
                result = await fn(*args, **kwargs)
                eid = _extract_entity_id(result, entity_id_key)
                await svc.record(
                    action=action,
                    status="SUCCESS",
                    actor_user_id=ctx.get("user_id"),
                    actor_username=None,
                    actor_ip=ctx.get("ip"),
                    request_id=ctx.get("request_id"),
                    http_method=ctx.get("method"),
                    http_path=ctx.get("path"),
                    entity_type=entity_type,
                    entity_id=eid,
                    meta={"args": str(args[1:]), "kwargs": kwargs if kwargs else None},
                )
                return result
            except Exception as ex:
                await svc.record(
                    action=action,
                    status="FAIL",
                    actor_user_id=ctx.get("user_id"),
                    actor_ip=ctx.get("ip"),
                    request_id=ctx.get("request_id"),
                    http_method=ctx.get("method"),
                    http_path=ctx.get("path"),
                    entity_type=entity_type,
                    entity_id=None,
                    meta={"error": str(ex)},
                )
                logger.exception("Audit FAIL for action: {}", action)
                raise
        return wrapper
    return decorator
