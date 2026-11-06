import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Item(Base):
    __tablename__ = "items"
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    channel_post_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(Enum("active", "closed", "cancelled", name="auction_status", create_type=False), default="active")
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    winner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    winning_bid: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Bid(Base):
    __tablename__ = "bids"
    bid_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.item_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    bid_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bid_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
