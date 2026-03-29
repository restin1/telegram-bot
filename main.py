import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

app = Client("rose_clone", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["rose_clone"]
warns = db["warns"]
notes = db["notes"]

# START BUTTON UI
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Rules", callback_data="rules")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    await message.reply("👋 Welcome to Advanced Group Bot", reply_markup=buttons)

# BUTTON HANDLER
@app.on_callback_query()
async def callback(client, query):
    if query.data == "rules":
        await query.message.edit("📜 Group Rules:\nNo spam\nNo links\nRespect all")
    elif query.data == "help":
        await query.message.edit("/ban /mute /warn /save /get")

# WARN SYSTEM
async def add_warn(user_id):
    user = await warns.find_one({"user_id": user_id})
    if user:
        count = user["count"] + 1
        await warns.update_one({"user_id": user_id}, {"$set": {"count": count}})
    else:
        count = 1
        await warns.insert_one({"user_id": user_id, "count": count})
    return count

@app.on_message(filters.command("warn") & filters.reply)
async def warn(client, message):
    user_id = message.reply_to_message.from_user.id
    count = await add_warn(user_id)
    await message.reply(f"⚠️ Warn {count}/3")

    if count >= 3:
        await message.chat.ban_member(user_id)
        await message.reply("🚫 Banned after 3 warns")

# BAN
@app.on_message(filters.command("ban") & filters.reply)
async def ban(client, message):
    user_id = message.reply_to_message.from_user.id
    await message.chat.ban_member(user_id)
    await message.reply("🚫 User banned")

# MUTE
@app.on_message(filters.command("mute") & filters.reply)
async def mute(client, message):
    user_id = message.reply_to_message.from_user.id
    await message.chat.restrict_member(
        user_id,
        ChatPermissions(can_send_messages=False)
    )
    await message.reply("🔇 User muted")

# NOTES SYSTEM
@app.on_message(filters.command("save"))
async def save_note(client, message):
    try:
        name = message.text.split(" ", 1)[1]
        reply = message.reply_to_message.text
        await notes.insert_one({"name": name, "text": reply})
        await message.reply("✅ Note saved")
    except:
        await message.reply("Reply to message: /save name")

@app.on_message(filters.command("get"))
async def get_note(client, message):
    try:
        name = message.text.split(" ", 1)[1]
        note = await notes.find_one({"name": name})
        if note:
            await message.reply(note["text"])
        else:
            await message.reply("❌ Note not found")
    except:
        await message.reply("Usage: /get name")

# ANTI-LINK
@app.on_message(filters.text & filters.group)
async def anti_link(client, message):
    if "http" in message.text or "t.me" in message.text:
        await message.delete()
        await message.reply("🚫 Links not allowed")

app.run()