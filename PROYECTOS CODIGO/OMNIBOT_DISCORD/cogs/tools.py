import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import glob

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spotify_download", description="Descarga una canción de Spotify y la envía al canal")
    async def spotify_download(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        try:
            # Run spotdl via subprocess
            process = await asyncio.create_subprocess_shell(
                f'spotdl "{url}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            # Find the downloaded file (assuming mp3, m4a, etc)
            files = glob.glob("*.mp3") + glob.glob("*.m4a") + glob.glob("*.ogg")
            # Sort by modified time to get the latest
            files.sort(key=os.path.getmtime, reverse=True)
            
            if files:
                latest_file = files[0]
                await interaction.followup.send(file=discord.File(latest_file))
                os.remove(latest_file)
            else:
                await interaction.followup.send("No se pudo encontrar el archivo descargado.")
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")

    @app_commands.command(name="ig_descargar", description="Descarga un post de Instagram")
    async def ig_descargar(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        try:
            import instaloader
            L = instaloader.Instaloader(dirname_pattern="ig_downloads")
            shortcode = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target=shortcode)
            
            # Send the first video or image found in the directory
            target_dir = f"ig_downloads/{shortcode}"
            if os.path.exists(target_dir):
                media_files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(('.mp4', '.jpg', '.png'))]
                if media_files:
                    # Discord limits file size (usually 8MB or 25MB), so we might hit it, but for now we just send the first
                    await interaction.followup.send(file=discord.File(media_files[0]))
                else:
                    await interaction.followup.send("Post descargado pero no se encontraron archivos multimedia.")
            else:
                await interaction.followup.send("Directorio de descarga no encontrado.")
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")

    @app_commands.command(name="texto_a_voz", description="Convierte texto a voz de alta calidad")
    async def texto_a_voz(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        try:
            output_file = "tts_output.mp3"
            process = await asyncio.create_subprocess_shell(
                f'edge-tts --text "{text}" --write-media {output_file}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if os.path.exists(output_file):
                await interaction.followup.send(file=discord.File(output_file))
                os.remove(output_file)
            else:
                await interaction.followup.send("Error al generar el audio.")
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")

    @app_commands.command(name="crear_meme", description="Agrega texto sobre un video")
    async def crear_meme(self, interaction: discord.Interaction, video_url: str, text: str):
        await interaction.response.defer()
        try:
            import urllib.request
            from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
            
            temp_video = "temp_input.mp4"
            output_video = "meme_output.mp4"
            
            req = urllib.request.Request(video_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(temp_video, 'wb') as out_file:
                out_file.write(response.read())
            
            video = VideoFileClip(temp_video)
            txt_clip = TextClip(text, fontsize=70, color='white')
            txt_clip = txt_clip.set_position('center').set_duration(video.duration)
            
            result = CompositeVideoClip([video, txt_clip])
            result.write_videofile(output_video, codec="libx264", audio_codec="aac")
            
            await interaction.followup.send(file=discord.File(output_video))
            
            video.close()
            if os.path.exists(temp_video): os.remove(temp_video)
            if os.path.exists(output_video): os.remove(output_video)
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")

    @app_commands.command(name="comparar_rostros", description="Compara dos imágenes para ver si es la misma persona")
    async def comparar_rostros(self, interaction: discord.Interaction, img1: discord.Attachment, img2: discord.Attachment):
        await interaction.response.defer()
        try:
            import face_recognition
            
            img1_path = "img1_temp.jpg"
            img2_path = "img2_temp.jpg"
            
            await img1.save(img1_path)
            await img2.save(img2_path)
            
            image_1 = face_recognition.load_image_file(img1_path)
            image_2 = face_recognition.load_image_file(img2_path)
            
            encoding_1 = face_recognition.face_encodings(image_1)
            encoding_2 = face_recognition.face_encodings(image_2)
            
            if not encoding_1 or not encoding_2:
                await interaction.followup.send("No se detectaron rostros en una o ambas imágenes.")
            else:
                results = face_recognition.compare_faces([encoding_1[0]], encoding_2[0])
                if results[0]:
                    await interaction.followup.send("✅ Las imágenes corresponden a la **MISMA** persona.")
                else:
                    await interaction.followup.send("❌ Las imágenes corresponden a **DIFERENTES** personas.")
                    
            if os.path.exists(img1_path): os.remove(img1_path)
            if os.path.exists(img2_path): os.remove(img2_path)
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")

async def setup(bot):
    await bot.add_cog(Tools(bot))
