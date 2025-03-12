import os
import discord
import dotenv
import time
from discord.ext import commands
from discord import app_commands

dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

TARGET_CHANNEL_ID = 605114288142811173

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

client = discord.Client(intents=intents)

# runs when bot is ready to go
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# runs when message is sent
# checks if message was sent from bot itself to prevent infinite looping
# otherwise, if message is '$newbot test' in botspam channel, responds with Hello!
@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return

    if message.channel.id == TARGET_CHANNEL_ID and message.content.startswith('$newbot test'):
        await message.channel.send('Hello!')

# TODO: listen for voice state changes
# if someone joins the main channel, play sound dependent on who it is
# if last person leaves main channel, disconnect from voice
# if first person joins main channel, connect to voice
@client.event
async def on_voice_state_update(member,before,after):
    defaultVal = 'None'
    beforeChannelId = before.channel.id if before.channel else -1
    afterChannelId = after.channel.id if after.channel else -1

    # returns if bot is the one that triggered it
    if member.id == client.user.id:
        return

    # returns if My Pants channel is not involved
    if beforeChannelId != 605114466719498263 and afterChannelId != 605114466719498263:
        print('My Pants channel was not involved')
        return

    # if someone mutes or deafens, do nothing
    if before.channel == after.channel:
        print('Nothing changed')
        return
    
    # someone joined channel
    if afterChannelId == 605114466719498263:
        print('Someone joined the channel.')
        joinedUserid = member.id
        vc = after.channel
        vcConnection = None
        if len(after.channel.members) == 1:
            print('Channel no longer empty.')
            print('Connecting to voice channel...')
            try:
                vcConnection = await vc.connect(timeout=15.0)
            except Exception as e:
                print(f'Couldn\'t connect: {e}')
                return
        vcConnection = client.voice_clients[0]
        soundpath = "./sounds/"
        time.sleep(0.6)
        match joinedUserid:
            case 110106223109496832:
                print('Josh joined')
                soundpath += "g.ogg"
            case 219653760312410113:
                print('Mark joined')
            case 113827762648776707:
                print('Austin joined')
            case 160800489737420800:
                print('Gio joined')
            case 340299484028207105:
                print('Alex joined')
            case 147562375971602432:
                print('Paul K joined')
                soundpath += "holymoly.ogg"
            case 160800395134763008:
                print('Tristen joined')
            case 213510490775617536:
                print('Shannon joined')
            case _:
                print('this guy needs a sound')
        
        if vcConnection and len(soundpath) > 9:
            vcConnection.play(discord.FFmpegPCMAudio(executable="./bin/ffmpeg/ffmpeg.exe",source=soundpath))
            

    # someone left channel
    if beforeChannelId == 605114466719498263:
        print('Someone left the channel')
        if len(before.channel.members) == 1: #when bot can actually connect, change this to 1
            print('Channel empty')
            print('Disconnecting from channel...')
            connectedVC = client.voice_clients[0]
            await connectedVC.disconnect()

    '''print(f'Member info: {member.id}')
    print(f'Before info: {before.channel.id if before.channel is not None else defaultVal}')
    print(f'After info: {after.channel.id if after.channel is not None else defaultVal}')
    print(f'More after info (user count): {len(after.channel.members) if after.channel is not None else 0}')'''

client.run(TOKEN)