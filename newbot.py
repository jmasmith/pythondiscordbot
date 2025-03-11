import os
import discord
import dotenv
from discord.ext import commands
from discord import app_commands

dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = 605114288142811173

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return

    if message.channel.id == TARGET_CHANNEL_ID and message.content.startswith('$newbot test'):
        await message.channel.send('Hello!')

client.run(TOKEN)