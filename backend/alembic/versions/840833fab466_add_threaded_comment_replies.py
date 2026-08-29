"""add threaded comment replies"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "840833fab466"
down_revision: Union[str, Sequence[str], None] = "925a25b89bf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clean up artifacts left by previous failed migration attempts
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_comments")
    op.execute("DROP INDEX IF EXISTS ix_comments_parent_comment_id")

    # Rebuild the comments table with the self-referencing FK
    with op.batch_alter_table(
        "comments",
        recreate="always"
    ) as batch_op:

        batch_op.create_foreign_key(
            "fk_comments_parent_comment_id",
            "comments",
            ["parent_comment_id"],
            ["id"]
        )

    # Recreate the index
    op.create_index(
        "ix_comments_parent_comment_id",
        "comments",
        ["parent_comment_id"]
    )

def downgrade() -> None:

    op.drop_index(
        "ix_comments_parent_comment_id",
        table_name="comments"
    )

    with op.batch_alter_table(
        "comments",
        recreate="always"
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_comments_parent_comment_id",
            type_="foreignkey"
        )