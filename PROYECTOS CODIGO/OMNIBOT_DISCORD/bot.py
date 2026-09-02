import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class OmniBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('/'),
            intents=intents,
            help_command=commands.DefaultHelpCommand()
        )

    async def setup_hook(self):
        # Load extensions
        initial_extensions = [
            'cogs.music',
            'cogs.osint',
            'cogs.ai_gen',
            'cogs.tools'
        ]
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension '{extension}'")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
        
        # Sync slash commands if we're using app_commands
        await self.tree.sync()
        logger.info("Synced application commands.")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')

if __name__ == '__main__':
    if not TOKEN:
        logger.error("No DISCORD_TOKEN provided. Please check your .env file.")
        exit(1)
        
    bot = OmniBot()
    bot.run(TOKEN)
