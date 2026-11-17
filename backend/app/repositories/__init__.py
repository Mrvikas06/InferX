"""Repositories Package."""

try:
    from backend.app.repositories.api_key_repository import (
        ApiKeyRepository,
        api_key_repository,
    )
    from backend.app.repositories.audit_log_repository import (
        AuditLogRepository,
        audit_log_repository,
    )
    from backend.app.repositories.base import BaseRepository
    from backend.app.repositories.deployment_repository import (
        DeploymentRepository,
        deployment_repository,
    )
    from backend.app.repositories.model_repository import (
        ModelRepository,
        model_repository,
    )
    from backend.app.repositories.user_repository import (
        UserRepository,
        user_repository,
    )
except (ImportError, ModuleNotFoundError):
    from app.repositories.api_key_repository import (
        ApiKeyRepository,
        api_key_repository,
    )
    from app.repositories.audit_log_repository import (
        AuditLogRepository,
        audit_log_repository,
    )
    from app.repositories.base import BaseRepository
    from app.repositories.deployment_repository import (
        DeploymentRepository,
        deployment_repository,
    )
    from app.repositories.model_repository import (
        ModelRepository,
        model_repository,
    )
    from app.repositories.user_repository import (
        UserRepository,
        user_repository,
    )

__all__ = [
    "BaseRepository",
    "ModelRepository",
    "model_repository",
    "DeploymentRepository",
    "deployment_repository",
    "UserRepository",
    "user_repository",
    "ApiKeyRepository",
    "api_key_repository",
    "AuditLogRepository",
    "audit_log_repository",
]
