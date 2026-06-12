import discord
from dotenv import load_dotenv
load_dotenv()
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

# ── Config ──────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
PREFIX = os.getenv("PREFIX", ".")

# ── Bot setup ────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ── MongoDB ──────────────────────────────────────────────
mongo_client = AsyncIOMotorClient(MONGO_URI)
bot.db = mongo_client["nsfw_bot"]

# ── Helpers ──────────────────────────────────────────────
def is_admin():
    async def predicate(ctx):
        return ctx.author.id in ADMIN_IDS
    return commands.check(predicate)

bot.is_admin = is_admin
bot.admin_ids = ADMIN_IDS

# ── Events ───────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[BOT] Logged in as {bot.user} ({bot.user.id})")
    await bot.load_extension("cogs.nsfw")
    await bot.load_extension("cogs.help")
    print("[BOT] Loaded cogs.nsfw")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Bạn không có quyền dùng lệnh này.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Thiếu tham số. Dùng `{PREFIX}nsfwhelp` để xem hướng dẫn.")
    else:
        print(f"[ERROR] {error}")

# ── Run ──────────────────────────────────────────────────
bot.run(TOKEN)
