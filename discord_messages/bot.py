import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

bot_token = os.getenv('bot_token')
assert bot_token != None, "No bot token to load from .env, create a bot in discord developer portal and get secret token"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


async def send_algorand_foundation_transaction_message(ctx, message: str):
    await ctx.send(message)


bot.run(bot_token)