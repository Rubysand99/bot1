import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="helpme")
    async def help_cmd(self, ctx):
        embed = discord.Embed(
            title="📖 Help Menu",
            color=0xff4444
        )
        embed.add_field(
            name="🔞 NSFW",
            value=(
                "`.nsfw [tags]` — lấy ảnh/gif/video\n"
                "`.nsfwhelp` — hướng dẫn chi tiết NSFW"
            ),
            inline=False
        )
        embed.add_field(
            name="⚙️ Admin",
            value=(
                "`.nsfwsetup channel #ch` — set channel auto-post\n"
                "`.nsfwsetup source <sources>` — chọn nguồn\n"
                "`.nsfwsetup tags <tags>` — filter tags\n"
                "`.nsfwsetup interval <phút>` — tần suất\n"
                "`.nsfwsetup start/stop` — bật/tắt auto-post\n"
                "`.nsfwsetup status` — xem config\n"
                "`.nsfwsetup clearseen` — xóa lịch sử"
            ),
            inline=False
        )
        embed.add_field(
            name="🌐 Nguồn hỗ trợ",
            value="`gelbooru` `rule34` `danbooru` `safebooru`",
            inline=False
        )
        embed.set_footer(text="⚠️ Lệnh NSFW chỉ dùng được trong NSFW channel")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
