"""
WhatsApp Web Voice Bot using Playwright, Coqui TTS, Deep Translator, and Google Gemini.
"""
import os
import time
import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
from deep_translator import GoogleTranslator
from TTS.api import TTS

# ---------------- CONFIGURATION ----------------
# Ensure you have set the GOOGLE_API_KEY environment variable.
# Example: os.environ["GOOGLE_API_KEY"] = "your_key"
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash"
NATIVE_LANGUAGE = "es" # Business native language (e.g., 'es' for Spanish, 'en' for English)

# Path to the reference audio file for voice cloning (needs to be ~10s of clear audio)
REFERENCE_AUDIO = "sample.wav"
OUTPUT_AUDIO_DIR = "generated_audio"

# Setup Output directory
if not os.path.exists(OUTPUT_AUDIO_DIR):
    os.makedirs(OUTPUT_AUDIO_DIR)

# ---------------- INITIALIZATION ----------------
print("Initializing TTS Model (this might take a while on first run)...")
# Using a model that supports voice cloning (e.g., xtts_v2)
# Note: Ensure you accept Coqui TTS terms if using xtts_v2
try:
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)
except Exception as e:
    print(f"Error initializing TTS: {e}")
    tts = None

def generate_reply(text: str) -> str:
    """Generates a professional reply using Google Gemini."""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = (
            "You are a professional customer support assistant for a business. "
            "Formulate a helpful, polite, and concise reply to the following customer message:\n\n"
            f"Customer: {text}\n\n"
            "Reply directly with the text response, without quotes or additional commentary."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I am currently unable to process your request."

def generate_voice(text: str, language: str) -> str:
    """Generates a cloned voice audio file from text."""
    if tts is None:
        return ""
    
    timestamp = int(time.time())
    output_path = os.path.join(OUTPUT_AUDIO_DIR, f"reply_{timestamp}.wav")
    
    # xtts_v2 expects language codes like 'en', 'es', 'fr', etc.
    try:
        tts.tts_to_file(text=text, speaker_wav=REFERENCE_AUDIO, language=language, file_path=output_path)
        return output_path
    except Exception as e:
        print(f"TTS Error: {e}")
        return ""

async def run_whatsapp_bot():
    """Runs the Playwright automation for WhatsApp Web."""
    async with async_playwright() as p:
        # We use a persistent context so we don't have to scan the QR code every time
        user_data_dir = os.path.join(os.getcwd(), "playwright_profile")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Must be False to scan QR code initially
        )
        
        page = await browser.new_page()
        print("Navigating to WhatsApp Web...")
        await page.goto("https://web.whatsapp.com/")
        print("Please scan the QR code if you haven't already.")
        
        # Wait until the chat list is visible (indicates successful login)
        await page.wait_for_selector('div[aria-label="Chat list"]', timeout=0)
        print("Successfully logged in!")

        processed_messages = set()

        while True:
            # Look for unread messages. This selector might need updates if WhatsApp Web changes.
            # A common approach is to look for the unread badge.
            unread_badges = await page.query_selector_all('span[aria-label*="unread message"]')
            
            for badge in unread_badges:
                try:
                    # Click the parent chat to open it
                    chat_element = await badge.evaluate_handle('node => node.closest("[role=\'listitem\']")')
                    if chat_element:
                        await chat_element.click()
                        await page.wait_for_timeout(1000) # Wait for chat to load
                        
                        # Get the last received message
                        messages = await page.query_selector_all('div.message-in span.selectable-text span')
                        if not messages:
                            continue
                            
                        last_message = await messages[-1].inner_text()
                        
                        if last_message in processed_messages:
                            continue
                            
                        processed_messages.add(last_message)
                        print(f"Received new message: {last_message}")

                        # 1. Translate incoming message if needed (detect language & translate to native)
                        # We use try/except as deep_translator might fail on empty strings
                        try:
                            # Let's assume we translate everything to native language to understand it
                            translated_in = GoogleTranslator(source='auto', target=NATIVE_LANGUAGE).translate(last_message)
                            print(f"Translated to native ({NATIVE_LANGUAGE}): {translated_in}")
                        except Exception:
                            translated_in = last_message

                        # 2. Formulate reply using LLM
                        reply_native = generate_reply(translated_in)
                        print(f"LLM Reply ({NATIVE_LANGUAGE}): {reply_native}")

                        # 3. Translate reply back to the user's language (if needed)
                        # For simplicity, we just generate the voice in the native language in this MVP.
                        
                        # 4. Voice Cloning
                        print("Generating voice audio...")
                        audio_path = generate_voice(reply_native, NATIVE_LANGUAGE)

                        # 5. Send Audio and/or Text back via WhatsApp
                        # For now, we will type the text. Uploading audio requires clicking the attachment button.
                        
                        # Send text
                        chat_input = await page.wait_for_selector('div[title="Type a message"]')
                        await chat_input.fill(reply_native)
                        await page.keyboard.press('Enter')
                        print("Text reply sent.")

                        # Send audio if generated successfully
                        if audio_path and os.path.exists(audio_path):
                            print(f"Uploading audio: {audio_path}")
                            # Click attach button
                            attach_btn = await page.wait_for_selector('div[title="Attach"]')
                            await attach_btn.click()
                            
                            # Document input is used for audio files to send them as playable voice notes/audio
                            # Using the hidden input file for documents:
                            file_input = await page.query_selector('input[accept="*"]')
                            if file_input:
                                await file_input.set_input_files(audio_path)
                                # Wait for preview to load and click send
                                send_btn = await page.wait_for_selector('div[aria-label="Send"]')
                                await send_btn.click()
                                print("Audio reply sent.")
                            else:
                                print("Could not find file input for attachment.")

                        await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"Error processing a message: {e}")

            # Polling interval
            await page.wait_for_timeout(3000)

if __name__ == "__main__":
    try:
        asyncio.run(run_whatsapp_bot())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
