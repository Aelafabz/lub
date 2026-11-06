import os
import asyncio
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy import text
from app.database import AsyncSessionLocal

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("publish"))
async def publish_item(message: Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        return

    if not command.args or "|" not in command.args:
        await message.answer("Usage: `/publish <Item Title> | <Duration in Hours>`", parse_mode="Markdown")
        return

    title, hours_str = [x.strip() for x in command.args.split("|", 1)]
    deadline = datetime.now(timezone.utc) + timedelta(hours=float(hours_str))

    async with AsyncSessionLocal() as db:
        async with db.begin():
            res = await db.execute(
                text("""
                    INSERT INTO items (title, deadline, status)
                    VALUES (:title, :deadline, 'active')
                    RETURNING item_id
                """),
                {"title": title, "deadline": deadline}
            )
            item_id = str(res.scalar())

            deep_link = f"https://t.me/{BOT_USERNAME}?start=item_{item_id}"
            channel_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔨 Place Lowest Unique Bid", url=deep_link)]
            ])

            post = await bot.send_message(
                chat_id=CHANNEL_ID,
                text=(
                    f"🔥 **NEW AUCTION LIVE!** 🔥\n\n"
                    f"📦 **Item:** {title}\n"
                    f"⏳ **Closes:** `{deadline.strftime('%Y-%m-%d %H:%M UTC')}`\n\n"
                    f"Click below to submit your lowest unique bid!"
                ),
                reply_markup=channel_kb,
                parse_mode="Markdown"
            )

            await db.execute(
                text("UPDATE items SET channel_post_id = :post_id WHERE item_id = :item_id"),
                {"post_id": post.message_id, "item_id": item_id}
            )

    await message.answer(f"✅ Published **{title}** (`{item_id}`) to channel.", parse_mode="Markdown")

@dp.message(CommandStart(deep_link=True))
async def handle_deep_link(message: Message, command: CommandObject):
    payload = command.args
    if not payload.startswith("item_"):
        await message.answer("Invalid auction link.")
        return

    item_id = payload.replace("item_", "")

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            text("SELECT title, status, deadline FROM items WHERE item_id = :item_id"),
            {"item_id": item_id}
        )
        item = res.mappings().first()

    if not item or item["status"] != "active":
        await message.answer("⚠️ This auction is closed or no longer available.")
        return

    target_webapp_url = f"{WEBAPP_URL}?item_id={item_id}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💳 Bid on {item['title']}",
            web_app=WebAppInfo(url=target_webapp_url)
        )]
    ])

    await message.answer(
        f"You are bidding on **{item['title']}**.\n"
        f"Deadline: `{item['deadline'].strftime('%Y-%m-%d %H:%M UTC')}`\n\n"
        f"Tap below to open the secure bidding terminal:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
