import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import logging

logger = logging.getLogger('discord.cogs.music')

# yt-dlp configuration
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {} # guild_id -> list of urls

    @app_commands.command(name="play", description="Play audio from a given URL (YouTube, Twitter, Reddit, etc.)")
    async def play(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("You are not connected to a voice channel.")
            return
            
        channel = interaction.user.voice.channel
        
        try:
            if interaction.guild.voice_client is None:
                await channel.connect()
            elif interaction.guild.voice_client.channel != channel:
                await interaction.guild.voice_client.move_to(channel)
        except Exception as e:
            await interaction.followup.send(f"Failed to connect to voice channel: {e}")
            return
            
        guild_id = interaction.guild.id
        if guild_id not in self.queues:
            self.queues[guild_id] = []
            
        vc = interaction.guild.voice_client
        
        if vc.is_playing():
            self.queues[guild_id].append(url)
            await interaction.followup.send(f"Added to queue: {url}")
        else:
            await self._play_song(interaction, url)

    async def _play_song(self, interaction: discord.Interaction, url: str):
        vc = interaction.guild.voice_client
        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            vc.play(player, after=lambda e: self.bot.loop.create_task(self._play_next(interaction)))
            await interaction.channel.send(f'Now playing: **{player.title}**')
        except Exception as e:
            logger.error(f"Error playing song: {e}")
            await interaction.channel.send(f"An error occurred: {e}")
            await self._play_next(interaction)

    async def _play_next(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in self.queues and len(self.queues[guild_id]) > 0:
            next_url = self.queues[guild_id].pop(0)
            await self._play_song(interaction, next_url)
        else:
            vc = interaction.guild.voice_client
            if vc and not vc.is_playing():
                await vc.disconnect()

    @app_commands.command(name="pause", description="Pause the current playing audio")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("Audio paused.")
        else:
            await interaction.response.send_message("Currently no audio is playing.")

    @app_commands.command(name="resume", description="Resume paused audio")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("Audio resumed.")
        else:
            await interaction.response.send_message("Audio is not paused.")

    @app_commands.command(name="skip", description="Skip the currently playing audio")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop() # This will trigger the 'after' callback in vc.play, which calls _play_next
            await interaction.response.send_message("Audio skipped.")
        else:
            await interaction.response.send_message("Currently no audio is playing.")
            
    @app_commands.command(name="queue", description="View the current audio queue")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in self.queues and self.queues[guild_id]:
            queue_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(self.queues[guild_id])])
            await interaction.response.send_message(f"**Current Queue:**\n{queue_list}")
        else:
            await interaction.response.send_message("The queue is empty.")

async def setup(bot):
    await bot.add_cog(Music(bot))
