"""ActivityStream Actor

Revision ID: 9f40b24a68be
Revises: 8bdea1b48f5d
Create Date: 2024-06-24 14:59:22.694484

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9f40b24a68be"
down_revision = "8bdea1b48f5d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "actor",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modified", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("fetched", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column(
            "type",
            postgresql.ENUM(
                "Application",
                "Group",
                "Organization",
                "Person",
                "Service",
                name="actortype",
                # create_type=False,
                checkfirst=True,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("preferredUsername", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("inbox", sa.String(), nullable=False),
        sa.Column("outbox", sa.String(), nullable=False),
        sa.Column("sharedInbox", sa.String(), nullable=True),
        sa.Column("following", sa.String(), nullable=True),
        sa.Column("followers", sa.String(), nullable=True),
        sa.Column("liked", sa.String(), nullable=True),
        sa.Column("URI", sa.String(), nullable=False),
        sa.Column("URL", sa.String(), nullable=True),
        sa.Column("privateKey", sa.String(), nullable=True),
        sa.Column("publicKey", sa.String(), nullable=False),
        sa.Column("publicKeyURI", sa.String(), nullable=False),
        sa.Column("creator_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["creator.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("URL"),
        sa.UniqueConstraint("followers"),
        sa.UniqueConstraint("following"),
        sa.UniqueConstraint("liked"),
        sa.UniqueConstraint("outbox"),
        sa.UniqueConstraint("privateKey"),
        sa.UniqueConstraint("publicKey"),
        sa.UniqueConstraint("publicKeyURI"),
    )
    op.create_index(op.f("ix_actor_URI"), "actor", ["URI"], unique=True)
    op.create_index(op.f("ix_actor_domain"), "actor", ["domain"], unique=False)
    op.create_index(op.f("ix_actor_id"), "actor", ["id"], unique=False)
    op.create_index(op.f("ix_actor_name"), "actor", ["name"], unique=False)
    op.create_index(op.f("ix_actor_preferredUsername"), "actor", ["preferredUsername"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_actor_preferredUsername"), table_name="actor")
    op.drop_index(op.f("ix_actor_name"), table_name="actor")
    op.drop_index(op.f("ix_actor_id"), table_name="actor")
    op.drop_index(op.f("ix_actor_domain"), table_name="actor")
    op.drop_index(op.f("ix_actor_URI"), table_name="actor")
    op.drop_table("actor")
    # ### end Alembic commands ###
