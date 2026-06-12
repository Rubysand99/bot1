import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timezone
from utils.booru import fetch_post, VALID_SOURCES

# ── Helpers ──────────────────────────────────────────────
def nsfw_only():
    async def predicate(ctx):
        if not ctx.channel.is_nsfw():
            await ctx.send("❌ Lệnh này chỉ dùng được trong NSFW channel.")
            return False
        return True
    return commands.check(predicate)


class NSFWCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.auto_post_loop.start()

    def cog_unload(self):
        self.auto_post_loop.cancel()

    # ── Lấy config của 1 guild ───────────────────────────
    async def get_config(self, guild_id: int) -> dict:
        doc = await self.db["nsfw_config"].find_one({"guild_id": guild_id})
        return doc or {}

    async def set_config(self, guild_id: int, data: dict):
        await self.db["nsfw_config"].update_one(
            {"guild_id": guild_id},
            {"$set": data},
            upsert=True
        )

    # ── Lấy seen_ids của guild ───────────────────────────
    async def get_seen(self, guild_id: int) -> set:
        doc = await self.db["nsfw_seen"].find_one({"guild_id": guild_id})
        return set(doc.get("ids", [])) if doc else set()

    async def add_seen(self, guild_id: int, post_id: str):
        await self.db["nsfw_seen"].update_one(
            {"guild_id": guild_id},
            {"$addToSet": {"ids": post_id}},
            upsert=True
        )

    # ── Gửi 1 post ra channel ────────────────────────────
    async def send_post(self, channel: discord.TextChannel, post: dict):
        if post["type"] == "video":
            # Discord tự embed video nếu gửi direct link
            await channel.send(f"📹 `{post['source']}` | {post['url']}")
        elif post["type"] == "gif":
            embed = discord.Embed(color=0xff4444)
            embed.set_image(url=post["url"])
            embed.set_footer(text=f"🔞 {post['source']}")
            await channel.send(embed=embed)
        else:
            embed = discord.Embed(color=0xff4444)
            embed.set_image(url=post["url"])
            embed.set_footer(text=f"🔞 {post['source']}")
            await channel.send(embed=embed)

    # ════════════════════════════════════════════════════
    # COMMANDS
    # ════════════════════════════════════════════════════

    @commands.command(name="nsfw")
    @nsfw_only()
    async def nsfw_cmd(self, ctx, *, tags: str = ""):
        """Lấy ảnh/gif/video NSFW. Dùng: .nsfw [tags]"""
        config = await self.get_config(ctx.guild.id)
        sources = config.get("sources", ["gelbooru", "rule34"])
        seen = await self.get_seen(ctx.guild.id)

        async with ctx.typing():
            post = await fetch_post(sources=sources, tags=tags, seen_ids=seen)

        if not post:
            await ctx.send("❌ Không tìm thấy nội dung phù hợp.")
            return

        await self.send_post(ctx.channel, post)
        await self.add_seen(ctx.guild.id, post["id"])

    @commands.command(name="nsfwsetup")
    async def nsfw_setup(self, ctx, option: str = "", *, value: str = ""):
        """Setup auto-post. Chỉ admin dùng được."""
        if ctx.author.id not in self.bot.admin_ids:
            await ctx.send("❌ Chỉ admin mới dùng được lệnh này.")
            return

        option = option.lower()

        # .nsfwsetup channel #channel
        if option == "channel":
            if not ctx.message.channel_mentions:
                await ctx.send("❌ Dùng: `.nsfwsetup channel #channel`")
                return
            ch = ctx.message.channel_mentions[0]
            if not ch.is_nsfw():
                await ctx.send("❌ Channel đó không phải NSFW channel.")
                return
            await self.set_config(ctx.guild.id, {"channel_id": ch.id})
            await ctx.send(f"✅ Đã set channel auto-post: {ch.mention}")

        # .nsfwsetup source gelbooru rule34 danbooru
        elif option == "source":
            chosen = [s.strip().lower() for s in value.split()]
            invalid = [s for s in chosen if s not in VALID_SOURCES]
            if invalid:
                await ctx.send(f"❌ Nguồn không hợp lệ: `{', '.join(invalid)}`\nValid: `{', '.join(VALID_SOURCES)}`")
                return
            await self.set_config(ctx.guild.id, {"sources": chosen})
            await ctx.send(f"✅ Nguồn đã chọn: `{', '.join(chosen)}`")

        # .nsfwsetup tags hentai anime ...
        elif option == "tags":
            await self.set_config(ctx.guild.id, {"tags": value.strip()})
            await ctx.send(f"✅ Tags đã set: `{value.strip() or '(none)'}`")

        # .nsfwsetup interval 30
        elif option == "interval":
            try:
                mins = int(value.strip())
                if mins < 5:
                    await ctx.send("❌ Interval tối thiểu 5 phút.")
                    return
            except ValueError:
                await ctx.send("❌ Dùng: `.nsfwsetup interval <số phút>`")
                return
            await self.set_config(ctx.guild.id, {"interval": mins})
            await ctx.send(f"✅ Interval: mỗi `{mins}` phút")

        # .nsfwsetup start
        elif option == "start":
            config = await self.get_config(ctx.guild.id)
            if not config.get("channel_id"):
                await ctx.send("❌ Chưa set channel. Dùng `.nsfwsetup channel #channel` trước.")
                return
            await self.set_config(ctx.guild.id, {"enabled": True})
            await ctx.send("✅ Auto-post đã bật!")

        # .nsfwsetup stop
        elif option == "stop":
            await self.set_config(ctx.guild.id, {"enabled": False})
            await ctx.send("✅ Auto-post đã tắt.")

        # .nsfwsetup status
        elif option == "status":
            config = await self.get_config(ctx.guild.id)
            ch_id = config.get("channel_id")
            ch = ctx.guild.get_channel(ch_id) if ch_id else None
            sources = config.get("sources", ["gelbooru", "rule34"])
            tags = config.get("tags", "(none)")
            interval = config.get("interval", 30)
            enabled = config.get("enabled", False)

            embed = discord.Embed(title="📋 NSFW Auto-post Config", color=0xff4444)
            embed.add_field(name="Status", value="🟢 Đang chạy" if enabled else "🔴 Đã tắt")
            embed.add_field(name="Channel", value=ch.mention if ch else "Chưa set")
            embed.add_field(name="Nguồn", value=", ".join(sources))
            embed.add_field(name="Tags", value=f"`{tags}`")
            embed.add_field(name="Interval", value=f"{interval} phút")
            await ctx.send(embed=embed)

        # .nsfwsetup clearseen
        elif option == "clearseen":
            await self.db["nsfw_seen"].delete_one({"guild_id": ctx.guild.id})
            await ctx.send("✅ Đã xóa danh sách đã gửi.")

        else:
            await ctx.send(
                f"**Các option của `.nsfwsetup`:**\n"
                f"`channel #channel` — set channel auto-post\n"
                f"`source gelbooru rule34 ...` — chọn nguồn\n"
                f"`tags [tags]` — filter tags\n"
                f"`interval [phút]` — tần suất (min 5 phút)\n"
                f"`start` — bật auto-post\n"
                f"`stop` — tắt auto-post\n"
                f"`status` — xem config hiện tại\n"
                f"`clearseen` — xóa lịch sử đã gửi"
            )

    @commands.command(name="nsfwhelp")
    async def nsfw_help(self, ctx):
        embed = discord.Embed(title="🔞 NSFW Bot — Hướng dẫn", color=0xff4444)
        embed.add_field(
            name="Commands",
            value=(
                "`.nsfw [tags]` — lấy ảnh/gif/video\n"
                "`.nsfwsetup ...` — cấu hình auto-post (admin)\n"
                "`.nsfwhelp` — hiện menu này"
            ),
            inline=False
        )
        embed.add_field(
            name="Nguồn hỗ trợ",
            value="`gelbooru` `rule34` `danbooru` `safebooru`",
            inline=False
        )
        embed.set_footer(text="⚠️ Chỉ hoạt động trong NSFW channel")
        await ctx.send(embed=embed)

    # ════════════════════════════════════════════════════
    # AUTO-POST LOOP
    # ════════════════════════════════════════════════════

    @tasks.loop(minutes=1)
    async def auto_post_loop(self):
        """Chạy mỗi phút, check từng guild xem đến giờ post chưa."""
        now_ts = int(datetime.now(timezone.utc).timestamp())

        async for config in self.db["nsfw_config"].find({"enabled": True}):
            guild_id = config.get("guild_id")
            channel_id = config.get("channel_id")
            interval = config.get("interval", 30)
            last_post = config.get("last_post", 0)

            if now_ts - last_post < interval * 60:
                continue

            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            sources = config.get("sources", ["gelbooru", "rule34"])
            tags = config.get("tags", "")
            seen = await self.get_seen(guild_id)

            try:
                post = await fetch_post(sources=sources, tags=tags, seen_ids=seen)
                if post:
                    await self.send_post(channel, post)
                    await self.add_seen(guild_id, post["id"])
                    await self.set_config(guild_id, {"last_post": now_ts})
            except Exception as e:
                print(f"[AUTO-POST] Guild {guild_id} error: {e}")

    @auto_post_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(NSFWCog(bot))
