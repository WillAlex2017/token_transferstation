import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    upstream_model: Mapped[str] = mapped_column(String(128), nullable=False)
    upstream_base_url: Mapped[str] = mapped_column(String(512), nullable=True)
    input_price: Mapped[float] = mapped_column(Numeric(12, 8), default=0.0)
    output_price: Mapped[float] = mapped_column(Numeric(12, 8), default=0.0)
    sell_input_price: Mapped[float] = mapped_column(Numeric(12, 8), default=0.0)
    sell_output_price: Mapped[float] = mapped_column(Numeric(12, 8), default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="active")
    rate_limit: Mapped[int] = mapped_column(default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
