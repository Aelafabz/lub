from decimal import Decimal
from uuid import UUID
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, condecimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import get_db
from app.auth import get_current_user
from app.bot import bot, dp
from app.worker import process_expired_auctions

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_expired_auctions, "interval", seconds=5, max_instances=1)
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    yield
    polling_task.cancel()
    scheduler.shutdown(wait=False)
    await redis_client.aclose()
    await bot.session.close()


app = FastAPI(title="LUB Processing API", lifespan=lifespan)

class BidRequest(BaseModel):
    item_id: UUID
    bid_amount: condecimal(gt=Decimal("0.00"), max_digits=10, decimal_places=2)

@app.get("/api/items/{item_id}")
async def get_item_details(item_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT item_id, title, status, deadline FROM items WHERE item_id = :item_id"),
        {"item_id": item_id}
    )
    item = result.mappings().first()
    if not item:
        raise HTTPException(status_code=404, detail="Auction item not found")
    return item

@app.post("/api/bids")
async def place_bid(
    payload: BidRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = int(user["id"])
    username = user.get("username", f"user_{user_id}")

    rate_key = f"rate_limit:bid:{user_id}"
    if await redis_client.exists(rate_key):
        raise HTTPException(status_code=429, detail="Slow down! Please wait before bidding again.")
    await redis_client.set(rate_key, "1", ex=2)

    async with db.begin():
        user_row = await db.execute(
            text("""
                INSERT INTO users (user_id, username)
                VALUES (:user_id, :username)
                ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username
                RETURNING is_banned
            """),
            {"user_id": user_id, "username": username}
        )
        if user_row.scalar():
            raise HTTPException(status_code=403, detail="User is banned from auctions.")

        item_row = await db.execute(
            text("""
                SELECT status, deadline FROM items
                WHERE item_id = :item_id
                FOR SHARE
            """),
            {"item_id": payload.item_id}
        )
        item = item_row.mappings().first()
        if not item:
            raise HTTPException(status_code=404, detail="Auction not found.")

        now = datetime.now(timezone.utc)
        if item["status"] != "active" or item["deadline"] <= now:
            raise HTTPException(status_code=400, detail="This auction has already ended.")

        try:
            await db.execute(
                text("""
                    INSERT INTO bids (item_id, user_id, bid_amount)
                    VALUES (:item_id, :user_id, :bid_amount)
                """),
                {
                    "item_id": payload.item_id,
                    "user_id": user_id,
                    "bid_amount": payload.bid_amount
                }
            )
        except Exception as e:
            if "idx_unique_user_item_bid" in str(e):
                raise HTTPException(status_code=409, detail="You already placed this exact bid amount.")
            raise HTTPException(status_code=500, detail="Could not register bid.")

    return {"status": "success", "message": f"Bid of ${payload.bid_amount:.2f} registered!"}


app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")
