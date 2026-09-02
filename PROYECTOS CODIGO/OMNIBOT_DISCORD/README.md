# OmniBot Discord Project

OmniBot is an advanced, production-ready Discord bot built in Python using `discord.py`. It integrates music playback from multiple sources, OSINT reverse face searching (simulated/mocked for educational purposes), and AI media generation.

## Features

- 🎵 **Music Cog (`cogs/music.py`)**: Play, pause, resume, skip, and queue audio from ANY video link supported by `yt-dlp` (YouTube, Twitter, Reddit, etc.).
- 🕵️ **OSINT Cog (`cogs/osint.py`)**: `/buscar_rostro` command to analyze a face image attachment and simulate matching in public databases, including a rigorous legal disclaimer.
- 🤖 **AI Gen Cog (`cogs/ai_gen.py`)**: Text-to-image and Text-to-Speech generation via `/generar_imagen` and `/generar_voz`. It uses a public image generation API and `gTTS` to save and send media locally.

## Prerequisites

- Python 3.9+
- FFmpeg installed and in your system PATH (required for audio playback in Discord).

## Setup Instructions

1. **Clone or Download** the repository.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Install FFmpeg** (if you haven't already):
   - Windows: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or use `winget install ffmpeg`.
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`
4. **Environment Variables**:
   - Rename `.env.example` to `.env`.
   - Add your bot token from the [Discord Developer Portal](https://discord.com/developers/applications) to `DISCORD_TOKEN`.
   - Add your Gemini API key (optional depending on extension) to `GEMINI_API_KEY`.
5. **Run the Bot**:
   ```bash
   python bot.py
   ```

## Discord Bot Configuration
Make sure your bot has the following intents enabled in the Discord Developer Portal:
- Message Content Intent
- Server Members Intent
- Voice States Intent
