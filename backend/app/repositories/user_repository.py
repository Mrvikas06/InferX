"""User Repository for InferX Authentication and Identity Management."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.core.security import hash_password
    from backend.app.models.user import User
    from backend.app.repositories.base import BaseRepository
    from backend.app.schemas.auth import UserRegister, UserUpdate
except (ImportError, ModuleNotFoundError):
    from app.core.security import hash_password
    from app.models.user import User
    from app.repositories.base import BaseRepository
    from app.schemas.auth import UserRegister, UserUpdate


class UserRepository(BaseRepository[User, UserRegister, UserUpdate]):
    """Data access repository for User entities."""

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        query = select(User).where(User.email == email.lower().strip())
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        payload: UserRegister,
        is_superuser: bool = False,
    ) -> User:
        """Create and persist a new user account with hashed password."""
        hashed = hash_password(payload.password)
        user = User(
            email=payload.email.lower().strip(),
            hashed_password=hashed,
            full_name=payload.full_name,
            role=payload.role.lower(),
            is_active=True,
            is_superuser=is_superuser,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user


user_repository = UserRepository(User)
