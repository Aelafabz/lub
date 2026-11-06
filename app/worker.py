import asyncio
from sqlalchemy import text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import AsyncSessionLocal
from app.bot import bot, CHANNEL_ID

async def process_expired_auctions():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            expired_rows = await db.execute(
                text("""
                    SELECT item_id, title, channel_post_id
                    FROM items
                    WHERE status = 'active' AND deadline <= CURRENT_TIMESTAMP
                    FOR UPDATE SKIP LOCKED
                """)
            )
            expired_items = expired_rows.mappings().all()

            for item in expired_items:
                item_id = item["item_id"]

                winner_res = await db.execute(
                    text("""
                        WITH unique_bids AS (
                            SELECT bid_amount
                            FROM bids
                            WHERE item_id = :item_id
                            GROUP BY bid_amount
                            HAVING COUNT(*) = 1
                            ORDER BY bid_amount ASC
                            LIMIT 1
                        )
                        SELECT b.user_id, u.username, b.bid_amount
                        FROM bids b
                        JOIN unique_bids ub ON b.bid_amount = ub.bid_amount
                        JOIN users u ON b.user_id = u.user_id
                        WHERE b.item_id = :item_id
                        LIMIT 1
                    """),
                    {"item_id": item_id}
                )
                winner = winner_res.mappings().first()

                if winner:
                    await db.execute(
                        text("""
                            UPDATE items
                            SET status = 'closed',
                                winner_user_id = :user_id,
                                winning_bid = :bid_amount
                            WHERE item_id = :item_id
                        """),
                        {
                            "user_id": winner["user_id"],
                            "bid_amount": winner["bid_amount"],
                            "item_id": item_id
                        }
                    )
                    try:
                        await bot.send_message(
                            chat_id=winner["user_id"],
                            text=f"🎉 **CONGRATULATIONS!** You won **{item['title']}** with the lowest unique bid of **${winner['bid_amount']:.2f}**!",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass

                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        reply_to_message_id=item["channel_post_id"],
                        text=(
                            f"🏁 **AUCTION CLOSED: {item['title']}**\n\n"
                            f"🏆 **Winner:** @{winner['username']}\n"
                            f"💎 **Lowest Unique Bid:** `${winner['bid_amount']:.2f}`"
                        ),
                        parse_mode="Markdown"
                    )
                else:
                    await db.execute(
                        text("UPDATE items SET status = 'closed' WHERE item_id = :item_id"),
                        {"item_id": item_id}
                    )
                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        reply_to_message_id=item["channel_post_id"],
                        text=f"🏁 **AUCTION CLOSED: {item['title']}**\n\nNo unique bids were found!",
                        parse_mode="Markdown"
                    )

async def start_worker():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_expired_auctions, "interval", seconds=5, max_instances=1)
    scheduler.start()
