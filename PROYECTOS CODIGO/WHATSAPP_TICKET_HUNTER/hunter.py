import time
import re
from playwright.sync_api import sync_playwright, TimeoutError

# ==============================================================================
# WARNING: WhatsApp Web DOM elements change frequently. 
# You may need to inspect the page and update these selectors over time.
# ==============================================================================
UNREAD_BADGE_SELECTOR = "span[aria-label*='unread message'], span[aria-label*='mensaje no leído']"
MESSAGE_IN_SELECTOR = "div.message-in span.selectable-text"
CHAT_BOX_SELECTOR = "div[contenteditable='true'][data-tab='10'], div[contenteditable='true'][title='Type a message'], div[contenteditable='true'][title='Escribe un mensaje']"
# ==============================================================================

def run(playwright):
    # Launch browser (headless=False so you can scan the QR code)
    browser = playwright.chromium.launch(headless=False)
    # Using a persistent context could avoid scanning QR every time, 
    # but for simplicity we start fresh in this version.
    context = browser.new_context()
    page = context.new_page()

    print("[*] Opening WhatsApp Web...")
    page.goto("https://web.whatsapp.com")

    print("[*] Waiting for user to scan QR code...")
    # Wait for the chat pane to appear, meaning login was successful
    page.wait_for_selector("div[id='pane-side']", timeout=0) 
    print("[+] Logged in successfully!")

    whatsapp_page = page

    while True:
        try:
            # Look for an unread message indicator
            unread_badge = whatsapp_page.locator(UNREAD_BADGE_SELECTOR).first

            if unread_badge.is_visible():
                print("[*] Unread message found! Opening chat...")
                unread_badge.click()
                time.sleep(2) # Give the chat pane time to render

                # Extract the last received message
                messages = whatsapp_page.locator(MESSAGE_IN_SELECTOR).all()
                if messages:
                    last_message = messages[-1].inner_text()
                    print(f"[-] Received message: {last_message}")

                    # Regex to find a URL in the message
                    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*')
                    match = url_pattern.search(last_message)

                    if match:
                        target_url = match.group(0)
                        print(f"[+] URL detected: {target_url}")
                        hunt_ticket(context, target_url, whatsapp_page)
                    else:
                        print("[-] No URL found in the latest message.")
            
            # Polling delay
            time.sleep(2)

        except Exception as e:
            print(f"[!] Error during polling cycle: {e}")
            time.sleep(5)

def hunt_ticket(context, target_url, whatsapp_page):
    """
    Opens a new tab with the target URL and searches for actionable buttons.
    """
    print(f"[*] Opening new tab for {target_url}...")
    ticket_page = context.new_page()
    try:
        ticket_page.goto(target_url, timeout=60000)
        print("[*] Hunting for the action button (Comprar/Reservar/Buy)...")
        
        button_found = False
        start_time = time.time()
        
        # Poll the page for up to 5 minutes to see if the button appears
        while time.time() - start_time < 300: 
            try:
                # Use Playwright's role-based locators to find buttons or links with specific text
                button = ticket_page.get_by_role("button", name=re.compile(r'(Comprar|Reservar|Buy)', re.IGNORECASE)).first
                if not button.is_visible():
                    button = ticket_page.get_by_role("link", name=re.compile(r'(Comprar|Reservar|Buy)', re.IGNORECASE)).first
                
                if button.is_visible():
                    print("[+] Action button found! Clicking it now...")
                    button.click()
                    button_found = True
                    break
            except Exception:
                pass # Ignore transient errors while waiting
            
            time.sleep(1) # Check every second
        
        if button_found:
            print("[+] Action completed. Notifying back via WhatsApp...")
            whatsapp_page.bring_to_front()
            
            # Locate the chat input box and send confirmation
            chat_box = whatsapp_page.locator(CHAT_BOX_SELECTOR).last
            if chat_box.is_visible():
                chat_box.click()
                chat_box.fill("Boleto/Cita conseguida!")
                chat_box.press("Enter")
                print("[+] Notification sent.")
            else:
                print("[!] Could not find WhatsApp chat box to send notification.")
        else:
            print("[-] Timeout: Target button not found on the page after 5 minutes.")

    except TimeoutError:
        print("[!] Failed to load the target URL in time.")
    finally:
        print("[*] Closing ticket tab...")
        ticket_page.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
