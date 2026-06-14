import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_cmd(self, ctx):
        embed = discord.Embed(
            title="📖 Help Menu",
            description="Prefix: `.`",
            color=0xff4444
        )
        embed.add_field(
            name="🔞 NSFW",
            value=(
                "`.nsfw` — lấy ảnh/gif/video ngẫu nhiên\n"
                "`.nsfw <tags>` — lấy theo tag cụ thể\n"
                "　*Chỉ dùng trong NSFW channel*"
            ),
            inline=False
        )
        embed.add_field(
            name="⚙️ Setup (Admin)",
            value=(
                "`.setup channel #ch` — set channel auto-post\n"
                "`.setup source <sources>` — chọn nguồn nội dung\n"
                "`.setup tags <tags>` — filter tag mặc định\n"
                "`.setup interval <phút>` — tần suất auto-post\n"
                "`.setup start` — bật auto-post\n"
                "`.setup stop` — tắt auto-post\n"
                "`.setup status` — xem cấu hình hiện tại\n"
                "`.setup clearseen` — xóa lịch sử đã gửi"
            ),
            inline=False
        )
        embed.add_field(
            name="🌐 Nguồn hỗ trợ",
            value="`gelbooru`  `rule34`  `danbooru`  `safebooru`",
            inline=False
        )
        embed.set_footer(text="⚠️ Lệnh NSFW chỉ hoạt động trong NSFW channel")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
