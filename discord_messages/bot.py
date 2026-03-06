import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')
channel_id_str = os.getenv('DISCORD_CHANNEL_ID') # Not server channel, the ID for the specific channel in the discord server
assert bot_token != None, "No bot token to load from .env, create a bot in discord developer portal and get secret token"
assert channel_id_str != None, "No discord channel to load from .env, get channel ID from any channel in discord server"

channel_id = int(channel_id_str)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


async def send_algorand_foundation_transaction_message(ctx: commands.Context, message: str = "Test"):
    channel = bot.get_channel(channel_id)
    if channel and isinstance(channel, (discord.TextChannel, discord.Thread)):
        await channel.send(message)
    else:
        await ctx.send("Invalid Channel ID")

@bot.command()
async def test(ctx: commands.Context):
    await ctx.send("Twitter Bot & Myself are online.")

if __name__ == "__main__":
    bot.run(bot_token)