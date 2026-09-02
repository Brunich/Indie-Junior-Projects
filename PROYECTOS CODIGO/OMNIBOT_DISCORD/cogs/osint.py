import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('discord.cogs.osint')

class OSINT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buscar_rostro", description="Busca un rostro en redes sociales o bases de datos OSINT (Simulado)")
    @app_commands.describe(imagen="La imagen del rostro a buscar")
    async def buscar_rostro(self, interaction: discord.Interaction, imagen: discord.Attachment):
        await interaction.response.defer()
        
        # Validate that it's an image
        if not imagen.content_type or not imagen.content_type.startswith('image/'):
            await interaction.followup.send("Por favor, adjunta un archivo de imagen válido.")
            return

        import os
        import aiohttp
        
        disclaimer = (
            "**⚠️ AVISO LEGAL Y DESCARGO DE RESPONSABILIDAD ⚠️**\n"
            "Esta herramienta es de uso estrictamente educativo y de investigación (OSINT).\n"
            "No asumas que los resultados son definitivos. El uso indebido para acoso o doxing está prohibido."
        )
        
        serpapi_key = os.getenv('SERPAPI_KEY')
        if not serpapi_key:
            await interaction.followup.send("⚠️ Error: La clave `SERPAPI_KEY` no está configurada en el servidor para realizar la búsqueda OSINT real.")
            return

        try:
            # Hacer petición real a SerpApi (Google Lens)
            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google_lens",
                "url": imagen.url,
                "api_key": serpapi_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        matches = data.get("visual_matches", [])
                        
                        if not matches:
                            await interaction.followup.send(f"🔍 **Análisis OSINT:**\nNo se encontraron coincidencias exactas en la web para esta imagen.\n\n{disclaimer}")
                            return
                            
                        # Format the top 3 results
                        result_message = f"🔍 **Análisis OSINT en Google Lens para la imagen:**\n🔗 [Enlace original]({imagen.url})\n\n**Mejores coincidencias encontradas:**\n"
                        for match in matches[:3]:
                            title = match.get('title', 'Sin título')
                            link = match.get('link', '#')
                            source = match.get('source', 'Fuente desconocida')
                            result_message += f"- 🟢 **{source}**: [{title}]({link})\n"
                            
                        result_message += f"\n{disclaimer}"
                        await interaction.followup.send(result_message)
                    else:
                        await interaction.followup.send("⚠️ Hubo un error de conexión con la API de búsqueda inversa.")
        except Exception as e:
            logger.error(f"Error en buscar_rostro: {e}")
            await interaction.followup.send("⚠️ Ocurrió un error inesperado al procesar la imagen.")

async def setup(bot):
    await bot.add_cog(OSINT(bot))
