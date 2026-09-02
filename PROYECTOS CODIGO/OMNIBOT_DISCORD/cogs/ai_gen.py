import discord
from discord.ext import commands
from discord import app_commands
import os
import aiohttp
import asyncio
from gtts import gTTS
import google.generativeai as genai
import tempfile
import logging

logger = logging.getLogger('discord.cogs.ai_gen')

class AIGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configure Gemini API if key is present
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)

    @app_commands.command(name="generar_imagen", description="Genera una imagen basada en tu prompt")
    @app_commands.describe(prompt="Descripción de la imagen que quieres generar")
    async def generar_imagen(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        
        # Using a free open API for image generation (pollinations.ai)
        try:
            enhanced_prompt = prompt
            if self.gemini_api_key:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    resp = model.generate_content(f"Mejora este prompt para generar una imagen espectacular, tradúcelo al inglés. Devuelve solo el prompt en inglés sin explicaciones: {prompt}")
                    if resp.text:
                        enhanced_prompt = resp.text.strip()
                except Exception as e:
                    logger.error(f"Gemini prompt error: {e}")
                    
            encoded_prompt = discord.utils.escape_markdown(enhanced_prompt).replace(' ', '%20')
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        
                        # Save the image locally
                        temp_dir = tempfile.gettempdir()
                        file_path = os.path.join(temp_dir, 'generated_image.png')
                        
                        with open(file_path, 'wb') as f:
                            f.write(data)
                            
                        # Send file to Discord
                        file = discord.File(file_path, filename="generated.png")
                        await interaction.followup.send(content=f"🎨 **Prompt:** {prompt}", file=file)
                        
                        # Clean up
                        os.remove(file_path)
                    else:
                        await interaction.followup.send("Hubo un error al generar la imagen.")
        except Exception as e:
            logger.error(f"Error in generar_imagen: {e}")
            await interaction.followup.send(f"Error generando la imagen: {str(e)}")

    @app_commands.command(name="generar_voz", description="Convierte texto a voz (TTS)")
    @app_commands.describe(texto="El texto que quieres convertir a voz", lang="Idioma (ej. 'es', 'en')")
    async def generar_voz(self, interaction: discord.Interaction, texto: str, lang: str = 'es'):
        await interaction.response.defer()
        
        try:
            enhanced_texto = texto
            if hasattr(self, 'gemini_api_key') and self.gemini_api_key:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    resp = model.generate_content(f"Mejora este texto para que suene como un asistente virtual carismático. Mantenlo corto. Devuelve solo el texto sin comillas ni explicaciones: {texto}")
                    if resp.text:
                        enhanced_texto = resp.text.strip()
                except Exception as e:
                    logger.error(f"Gemini TTS error: {e}")

            # Generate TTS in a separate thread to avoid blocking
            def run_tts(text_to_speak):
                tts = gTTS(text=text_to_speak, lang=lang)
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, 'tts_output.mp3')
                tts.save(output_path)
                return output_path
                
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(None, run_tts, enhanced_texto)
            
            # Send file to Discord
            file = discord.File(file_path, filename="tts.mp3")
            await interaction.followup.send(content=f"🗣️ **Texto:** {texto}", file=file)
            
            # Clean up
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error in generar_voz: {e}")
            await interaction.followup.send(f"Error generando la voz: {str(e)}")

async def setup(bot):
    await bot.add_cog(AIGen(bot))
