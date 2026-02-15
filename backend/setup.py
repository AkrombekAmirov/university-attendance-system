import asyncio
from backend.core.config import get_settings
from backend.core.DatabaseService.base import DatabaseService
from backend.domain.organization.models import Organization
from backend.core.security import get_password_hash
from sqlmodel import SQLModel
from backend.domain.user.models import User
import uuid

async def create_superadmin():
    settings = get_settings()
    db = DatabaseService()
    engine = db.session_scope()
    async with db.session_scope() as session:
        org = Organization(
            id=str(uuid.uuid4()),
            name="Nizomiy nomidagi O'zbekiston milliy pedagogika universiteti",
            code="2025",

        )
        user = User(
            id=str(uuid.uuid4()),
            username="admin",
            full_name="System Administrator",
            email="admin@example.com",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
            is_superadmin=True,
            created_by="system",
        )
        session.add(user)
        session.add(org)
        await session.commit()
        print("✅ Superadmin created successfully!")

if __name__ == "__main__":
    asyncio.run(create_superadmin())
