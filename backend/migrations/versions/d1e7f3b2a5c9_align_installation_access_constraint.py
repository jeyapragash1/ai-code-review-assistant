"""align installation access constraint naming

Revision ID: d1e7f3b2a5c9
Revises: c8d6e2a1f4b0
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d1e7f3b2a5c9"
down_revision: str | Sequence[str] | None = "c8d6e2a1f4b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_installation_repository_access_installation_id", "installation_repository_access", type_="unique")
    op.create_unique_constraint(
        "uq_installation_repository_access_installation_id_repository_id",
        "installation_repository_access",
        ["installation_id", "repository_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_installation_repository_access_installation_id_repository_id", "installation_repository_access", type_="unique")
    op.create_unique_constraint(
        "uq_installation_repository_access_installation_id",
        "installation_repository_access",
        ["installation_id", "repository_id"],
    )
