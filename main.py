# ── DNS Fix ──
import dns.resolver
_resolver = dns.resolver.Resolver(configure=False)
_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]
dns.resolver.default_resolver = _resolver

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# load_dotenv TRƯỚC khi đọc bất kỳ biến môi trường nào
load_dotenv('/data/data/com.termux/files/home/bot1/.env')

TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
PREFIX = os.getenv("BOT_PREFIX", ".")

print(f"[CONFIG] PREFIX={repr(PREFIX)}")

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.admin_ids = ADMIN_IDS
        self.db = AsyncIOMotorClient(MONGO_URI)["nsfw_bot"]

    async def setup_hook(self):
        await self.load_extension("cogs.nsfw")
        await self.load_extension("cogs.help")
        print("[BOT] All cogs loaded")

    async def on_ready(self):
        print(f"[BOT] Logged in as {self.user} ({self.user.id})")
        print(f"[BOT] PREFIX={repr(self.command_prefix)}")
        print(f"[BOT] Commands: {[c.name for c in self.commands]}")

    async def on_message(self, message):
        if message.author.bot:
            return
        print(f"[MSG] #{message.channel} {message.author}: {message.content!r}")
        ctx = await self.get_context(message)
        print(f"[CTX] valid={ctx.valid} command={ctx.command}")
        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print(f"[CHECK-FAIL] {ctx.command} | {error}")
            await ctx.send("❌ Bạn không có quyền dùng lệnh này.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Thiếu tham số. Dùng `{PREFIX}help` để xem hướng dẫn.")
        else:
            print(f"[ERROR] {type(error).__name__}: {error}")

def is_admin():
    async def predicate(ctx):
        return ctx.author.id in ctx.bot.admin_ids
    return commands.check(predicate)

bot = MyBot()
bot.is_admin = is_admin

bot.run(TOKEN)
