"""Create privacy configuration tables and development bootstrap."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260831_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("active_model_id", sa.String(200), nullable=True),
    )
    op.create_table(
        "model_mappings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_id", sa.String(200), nullable=False),
        sa.Column("native_entity_type", sa.String(200), nullable=False),
        sa.Column("canonical_type", sa.String(100), nullable=False),
        sa.UniqueConstraint("model_id", "native_entity_type"),
    )
    op.create_index("ix_model_mappings_model_id", "model_mappings", ["model_id"])
    op.create_table(
        "pattern_recognizers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("canonical_type", sa.String(100), nullable=False),
        sa.Column("patterns", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("context_words", sa.JSON(), nullable=False),
        sa.Column("validator", sa.String(100), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "gazetteers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("canonical_type", sa.String(100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("case_sensitive", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "gazetteer_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "gazetteer_id",
            sa.Integer(),
            sa.ForeignKey("gazetteers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value", sa.Text(), nullable=False),
        sa.UniqueConstraint("gazetteer_id", "value"),
    )
    op.create_index(
        "ix_gazetteer_entries_gazetteer_id",
        "gazetteer_entries",
        ["gazetteer_id"],
    )
    op.create_table(
        "detection_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("model_enabled", sa.Boolean(), nullable=False),
        sa.Column("pattern_enabled", sa.Boolean(), nullable=False),
        sa.Column("gazetteer_enabled", sa.Boolean(), nullable=False),
        sa.Column("source_priority", sa.JSON(), nullable=False),
    )
    op.create_table(
        "protection_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("canonical_type", sa.String(100), nullable=False, unique=True),
        sa.Column("action", sa.String(50), nullable=False),
    )

    system_settings = sa.table(
        "system_settings",
        sa.column("id", sa.Integer()),
        sa.column("active_model_id", sa.String()),
    )
    op.bulk_insert(
        system_settings,
        [{"id": 1, "active_model_id": "openmed-pii-spanish-600m"}],
    )

    mappings = sa.table(
        "model_mappings",
        sa.column("model_id", sa.String()),
        sa.column("native_entity_type", sa.String()),
        sa.column("canonical_type", sa.String()),
    )
    safe_mappings = {
        "ACCOUNTNAME": "USERNAME",
        "AGE": "AGE",
        "CITY": "LOCATION",
        "COUNTY": "LOCATION",
        "DATE": "DATE",
        "DATEOFBIRTH": "DATE",
        "EMAIL": "EMAIL",
        "FIRSTNAME": "PERSON_NAME",
        "LASTNAME": "PERSON_NAME",
        "MIDDLENAME": "PERSON_NAME",
        "PHONE": "PHONE",
        "SECONDARYADDRESS": "STREET_ADDRESS",
        "STATE": "LOCATION",
        "STREET": "STREET_ADDRESS",
        "USERNAME": "USERNAME",
    }
    op.bulk_insert(
        mappings,
        [
            {
                "model_id": "openmed-pii-spanish-600m",
                "native_entity_type": native,
                "canonical_type": canonical,
            }
            for native, canonical in safe_mappings.items()
        ],
    )

    recognizers = sa.table(
        "pattern_recognizers",
        sa.column("name", sa.String()),
        sa.column("canonical_type", sa.String()),
        sa.column("patterns", sa.JSON()),
        sa.column("score", sa.Float()),
        sa.column("context_words", sa.JSON()),
        sa.column("validator", sa.String()),
        sa.column("enabled", sa.Boolean()),
    )
    op.bulk_insert(
        recognizers,
        [
            {
                "name": "Email address",
                "canonical_type": "EMAIL",
                "patterns": [r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"],
                "score": 0.95,
                "context_words": [],
                "validator": None,
                "enabled": True,
            },
            {
                "name": "Ecuador phone",
                "canonical_type": "PHONE",
                "patterns": [r"(?<!\d)(?:\+593[ -]?|0)(?:9\d{8}|[2-7]\d{7})(?!\d)"],
                "score": 0.9,
                "context_words": ["telefono", "teléfono", "celular", "contacto"],
                "validator": None,
                "enabled": True,
            },
            {
                "name": "Ecuador national ID",
                "canonical_type": "NATIONAL_ID",
                "patterns": [r"(?<!\d)\d{10}(?!\d)"],
                "score": 0.98,
                "context_words": ["cedula", "cédula", "identificacion", "identificación"],
                "validator": "ecuador_national_id",
                "enabled": True,
            },
        ],
    )

    detection_settings = sa.table(
        "detection_settings",
        sa.column("id", sa.Integer()),
        sa.column("threshold", sa.Float()),
        sa.column("model_enabled", sa.Boolean()),
        sa.column("pattern_enabled", sa.Boolean()),
        sa.column("gazetteer_enabled", sa.Boolean()),
        sa.column("source_priority", sa.JSON()),
    )
    op.bulk_insert(
        detection_settings,
        [
            {
                "id": 1,
                "threshold": 0.5,
                "model_enabled": True,
                "pattern_enabled": True,
                "gazetteer_enabled": True,
                "source_priority": ["PATTERN", "GAZETTEER", "MODEL"],
            }
        ],
    )

    rules = sa.table(
        "protection_rules",
        sa.column("canonical_type", sa.String()),
        sa.column("action", sa.String()),
    )
    op.bulk_insert(
        rules,
        [
            {"canonical_type": "PII", "action": "MASK"},
            {"canonical_type": "PERSON_NAME", "action": "PSEUDONYMIZE"},
            {"canonical_type": "EMAIL", "action": "PSEUDONYMIZE"},
            {"canonical_type": "PHONE", "action": "PSEUDONYMIZE"},
            {"canonical_type": "USERNAME", "action": "PSEUDONYMIZE"},
            {"canonical_type": "NATIONAL_ID", "action": "PSEUDONYMIZE"},
            {"canonical_type": "STUDENT_ID", "action": "PSEUDONYMIZE"},
        ],
    )


def downgrade() -> None:
    op.drop_table("protection_rules")
    op.drop_table("detection_settings")
    op.drop_index("ix_gazetteer_entries_gazetteer_id", table_name="gazetteer_entries")
    op.drop_table("gazetteer_entries")
    op.drop_table("gazetteers")
    op.drop_table("pattern_recognizers")
    op.drop_index("ix_model_mappings_model_id", table_name="model_mappings")
    op.drop_table("model_mappings")
    op.drop_table("system_settings")
