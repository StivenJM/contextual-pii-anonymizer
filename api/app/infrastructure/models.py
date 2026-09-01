from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SystemSettingModel(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    active_model_id: Mapped[str | None] = mapped_column(String(200), nullable=True)


class ModelMappingModel(Base):
    __tablename__ = "model_mappings"
    __table_args__ = (UniqueConstraint("model_id", "native_entity_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(String(200), index=True)
    native_entity_type: Mapped[str] = mapped_column(String(200))
    canonical_type: Mapped[str] = mapped_column(String(100))


class PatternRecognizerModel(Base):
    __tablename__ = "pattern_recognizers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    canonical_type: Mapped[str] = mapped_column(String(100))
    patterns: Mapped[list[str]] = mapped_column(JSON)
    score: Mapped[float] = mapped_column(Float)
    context_words: Mapped[list[str]] = mapped_column(JSON, default=list)
    validator: Mapped[str | None] = mapped_column(String(100), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class GazetteerModel(Base):
    __tablename__ = "gazetteers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    canonical_type: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float, default=0.85)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    entries: Mapped[list["GazetteerEntryModel"]] = relationship(
        back_populates="gazetteer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GazetteerEntryModel(Base):
    __tablename__ = "gazetteer_entries"
    __table_args__ = (UniqueConstraint("gazetteer_id", "value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gazetteer_id: Mapped[int] = mapped_column(
        ForeignKey("gazetteers.id", ondelete="CASCADE"),
        index=True,
    )
    value: Mapped[str] = mapped_column(Text)
    gazetteer: Mapped[GazetteerModel] = relationship(back_populates="entries")


class DetectionSettingsModel(Base):
    __tablename__ = "detection_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    threshold: Mapped[float] = mapped_column(Float)
    model_enabled: Mapped[bool] = mapped_column(Boolean)
    pattern_enabled: Mapped[bool] = mapped_column(Boolean)
    gazetteer_enabled: Mapped[bool] = mapped_column(Boolean)
    source_priority: Mapped[list[str]] = mapped_column(JSON)


class ProtectionRuleModel(Base):
    __tablename__ = "protection_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_type: Mapped[str] = mapped_column(String(100), unique=True)
    action: Mapped[str] = mapped_column(String(50))
