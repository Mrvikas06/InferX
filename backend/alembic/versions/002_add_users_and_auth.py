"""Add users table and RBAC foreign keys to API keys and audit logs.

Revision ID: 002_add_users_and_auth
Revises: 001_initial_schema
Create Date: 2026-11-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_users_and_auth"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    # 2. Add role and user_id to api_keys
    op.add_column("api_keys", sa.Column("role", sa.String(length=32), server_default="operator", nullable=False))
    op.add_column("api_keys", sa.Column("user_id", sa.String(length=36), nullable=True))
    op.create_index(op.f("ix_api_keys_role"), "api_keys", ["role"], unique=False)
    op.create_index(op.f("ix_api_keys_user_id"), "api_keys", ["user_id"], unique=False)
    op.create_foreign_key("fk_api_keys_user_id", "api_keys", "users", ["user_id"], ["id"], ondelete="SET NULL")

    # 3. Add actor_id and status to audit_logs
    op.add_column("audit_logs", sa.Column("actor_id", sa.String(length=64), nullable=True))
    op.add_column("audit_logs", sa.Column("status", sa.String(length=32), server_default="success", nullable=False))
    op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_status"), "audit_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_status"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_id"), table_name="audit_logs")
    op.drop_column("audit_logs", "status")
    op.drop_column("audit_logs", "actor_id")

    op.drop_constraint("fk_api_keys_user_id", "api_keys", type_="foreignkey")
    op.drop_index(op.f("ix_api_keys_user_id"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_role"), table_name="api_keys")
    op.drop_column("api_keys", "user_id")
    op.drop_column("api_keys", "role")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
