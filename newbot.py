import os
import discord
import dotenv
import time
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
from collections import deque


dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

SONG_QUEUES = {}

async def search_ytdlp_async(query,ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None,lambda: _extract(query,ydl_opts))

def _extract(query,ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # if this doesn't work, pull it out of the sanitize_info function
        return ydl.sanitize_info(ydl.extract_info(query,download=False))

GUILD_ID = "604123366974160914"
TARGET_CHANNEL_ID = 605114288142811173
VOICE_CHANNEL_ID = 605114466719498263

# global variable for the music playing feature
#playingMusic = False

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

client = commands.Bot(command_prefix="$",intents=intents)

# runs when bot is ready to go
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# command to play youtube music
@client.tree.command(name="play",description="looks for song on youtube and plays/queues it")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query:str):
    await interaction.response.defer()
    vc = interaction.user.voice
    username = interaction.user.mention

    if vc is None or vc.channel.id != VOICE_CHANNEL_ID:
        await interaction.followup.send("You gotta be in the No Pants channel, stupid")
        return
    
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await vc.channel.connect()
    
    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query,ydl_options)
    tracks = results.get("entries",[])
    
    if tracks is None:
        await interaction.followup.send("No results found")
        return
    
    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title","Untitled")

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    SONG_QUEUES[guild_id].append((audio_url,title))

    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added to queue: **{title}**")
    else:
        await interaction.followup.send(f"Now playing: **{title}**")
        await play_next(voice_client,guild_id,interaction.channel)

    '''
    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -c:a libopus -b:a 96k",
    }

    source = discord.FFmpegOpusAudio(audio_url,**ffmpeg_options,executable="./bin/ffmpeg/ffmpeg.exe")

    voice_client.play(source)
    await interaction.followup.send(f"Playing: {title}")
    '''

    #await interaction.response.send_message(f"This command doesn't do anything yet, {username}")

@client.tree.command(name="skip",description="Skips currently playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped current song")
    else:
        await interaction.response.send_message("Nothing to skip, idiot")

@client.tree.command(name="pause",description="Pauses the current song")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("I'm not in any voice channels bitch")
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is playing")
    
    voice_client.pause()
    await interaction.response.send_message("Song paused")

@client.tree.command(name="resume",description="Resumes the current song in queue")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("I'm not in any voice channels bitch")
    if not voice_client.is_paused():
        return await interaction.response.send_message("I'm not paused")
    
    voice_client.resume()
    await interaction.response.send_message("Song resumed")

@client.tree.command(name="stop",description="Stops playback and clears queue")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client

    if not voice_client or not voice_client.is_connected():
        return await interaction.followup.send("I'm not in any voice channels bitch")
    
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await interaction.followup.send("Stopped playback and cleared the queue")

# syncs the command tree
@client.event
async def on_message(message):
    if message.author.id == client.user.id or message.author.id != 110106223109496832:
        return

    if message.channel.id == TARGET_CHANNEL_ID and message.content.startswith('$syncTree'):
        guild = message.guild
        await client.tree.sync(guild=guild)
        await message.channel.send('Command tree synced')

# TODO: listen for voice state changes
# if someone joins the main channel, play sound dependent on who it is
# if last person leaves main channel, disconnect from voice
# if first person joins main channel, connect to voice
@client.event
async def on_voice_state_update(member,before,after):
    defaultVal = 'None'
    guild_id_str = GUILD_ID
    beforeChannelId = before.channel.id if before.channel else -1
    afterChannelId = after.channel.id if after.channel else -1

    # returns if bot is the one that triggered it
    if member.id == client.user.id:
        return

    # returns if My Pants channel is not involved
    if beforeChannelId != VOICE_CHANNEL_ID and afterChannelId != VOICE_CHANNEL_ID:
        print('My Pants channel was not involved')
        return

    # if someone mutes or deafens, do nothing
    if before.channel == after.channel:
        print('Nothing changed')
        return
    
    # someone joined channel
    if afterChannelId == VOICE_CHANNEL_ID:
        print('Someone joined the channel.')
        
        joinedUserid = member.id
        vc = after.channel

        vcConnection = client.voice_clients[0] if len(client.voice_clients) > 0 else None

        if len(after.channel.members) >= 1 and vcConnection is None:
            print('Channel no longer empty.')
            print('Connecting to voice channel...')
            try:
                vcConnection = await vc.connect(timeout=15.0)
            except Exception as e:
                print(f'Couldn\'t connect: {e}')
                return
            
        # vcConnection = client.voice_clients[0]
        soundpath = "./sounds/"

        time.sleep(0.6)
        match joinedUserid:
            case 110106223109496832:
                print('Josh joined')
                soundpath += "g.ogg"
            case 219653760312410113:
                print('Mark joined')
                soundpath += "fortnite.ogg"
            case 113827762648776707:
                print('Austin joined')
                soundpath += "brothaeugh.ogg"
            case 160800489737420800:
                print('Gio joined')
                soundpath += "goopman.mp3"
            case 340299484028207105:
                print('Alex joined')
                soundpath += "alex.ogg"
            case 147562375971602432:
                print('Paul K joined')
                soundpath += "holymoly.ogg"
            case 160800395134763008:
                print('Tristen joined')
                soundpath += "tristen.mp3"
            case 213510490775617536:
                print('Shannon joined')
            case _:
                print('this guy needs a sound')
        
        if vcConnection and len(soundpath) > 9 and not vcConnection.is_playing():
            try:
                vcConnection.play(discord.FFmpegPCMAudio(executable="./bin/ffmpeg/ffmpeg.exe",source=soundpath))
            except Exception as e:
                print(f"Couldn't play sound. Error: {e}")

        # check if any songs are queued
        
        if SONG_QUEUES.get(guild_id_str) is not None:
            botspamChannel = client.get_channel(605114288142811173)
            await play_next(vcConnection,guild_id_str,botspamChannel)
        
        return
            

    # someone left channel
    if beforeChannelId == VOICE_CHANNEL_ID:
        print('Someone left the channel')
        if len(before.channel.members) == 1 and len(client.voice_clients) > 0: #when bot can actually connect, change this to 1
            print('Channel empty')
            print('Disconnecting from channel...')
            connectedVC = client.voice_clients[0]
            SONG_QUEUES[guild_id_str].clear()
            await connectedVC.disconnect()
        return

async def play_next(voice_client,guild_id,channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }
        source = discord.FFmpegOpusAudio(audio_url,**ffmpeg_options,executable="./bin/ffmpeg/ffmpeg.exe")

        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next(voice_client,guild_id,channel),client.loop)

        voice_client.play(source,after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))
    else:
        SONG_QUEUES[guild_id] = deque()

client.run(TOKEN)