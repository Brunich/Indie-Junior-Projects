import os
import random
import logging
from typing import Dict, Any

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
CSV_PATH = 'population_data.csv'
WARNING_LOG_PATH = 'warning.log'

def setup_warning_logger():
    """Sets up a specific logger for warnings regarding synthetic data."""
    warning_logger = logging.getLogger('synthetic_warnings')
    warning_logger.setLevel(logging.WARNING)
    fh = logging.FileHandler(WARNING_LOG_PATH)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    warning_logger.addHandler(fh)
    return warning_logger

warning_logger = setup_warning_logger()

def load_data() -> pd.DataFrame:
    """
    Attempts to load population data from the CSV file.
    Returns None if the file is missing or empty.
    """
    if not os.path.exists(CSV_PATH):
        return None
    try:
        df = pd.read_csv(CSV_PATH)
        if df.empty:
            return None
        return df
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return None

def generate_synthetic_data() -> Dict[str, Any]:
    """Generates random demographic data if CSV is unavailable."""
    # Write explicit warning to warning.log
    warning_logger.warning("WARNING: population_data.csv is missing or empty. Using SYNTHETIC random entropy data.")
    logger.warning("Using synthetic data. Check warning.log.")
    
    return {
        'age': random.randint(18, 70),
        'gender': random.choice(['Male', 'Female', 'Non-binary', 'Prefer not to say']),
        'favorite_color': random.choice(['Red', 'Blue', 'Green', 'Black', 'White']),
        'satisfaction': random.randint(1, 5),
        'tech_savvy': random.choice(['Yes', 'No']),
        'comments': random.choice([
            "It's okay I guess.",
            "Needs improvement.",
            "Looks good to me.",
            "No strong opinion.",
            "Could be better."
        ])
    }

def get_profile() -> Dict[str, Any]:
    """Retrieves a profile from CSV or generates a synthetic one."""
    df = load_data()
    if df is not None:
        # Pick a random row
        profile = df.sample(n=1).iloc[0].to_dict()
        logger.info(f"Loaded profile from CSV: {profile}")
        return profile
    else:
        profile = generate_synthetic_data()
        logger.info(f"Generated synthetic profile: {profile}")
        return profile

def fill_survey(url: str):
    """
    Automates the process of filling out a survey using Playwright.
    Note: Selectors are examples and would need to be adapted to the specific survey form.
    """
    profile = get_profile()
    
    with sync_playwright() as p:
        # Launch browser (headless=False for demonstration/debugging)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            logger.info(f"Navigating to {url}")
            page.goto(url, wait_until="networkidle")
            
            # --- EXAMPLE INTERACTION LOGIC ---
            # The following selectors are purely hypothetical.
            # In a real scenario, you must inspect the DOM of Google Forms or SurveyMonkey.
            
            logger.info("Filling form fields...")
            
            # Example: Fill Age
            # page.fill('input[name="age_field"]', str(profile['age']))
            # page.wait_for_timeout(random.randint(500, 1500))
            
            # Example: Select Gender (Radio button)
            # page.click(f'label:has-text("{profile["gender"]}")')
            # page.wait_for_timeout(random.randint(500, 1500))
            
            # Example: Fill Comments (Textarea)
            # page.fill('textarea[name="comments_field"]', profile['comments'])
            # page.wait_for_timeout(random.randint(500, 1500))
            
            # Example: Click Submit
            # page.click('button[type="submit"]')
            # page.wait_for_navigation()
            
            logger.info("Form filled successfully. (Simulation completed)")
            
        except PlaywrightTimeoutError:
            logger.error("Timeout occurred while trying to find an element or load the page.")
        except Exception as e:
            logger.error(f"An error occurred during automation: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    # Example usage
    # Replace with an actual Google Form or SurveyMonkey URL for testing
    SURVEY_URL = "https://example.com/dummy-survey"
    logger.info("Starting Survey Population Bot...")
    fill_survey(SURVEY_URL)
    logger.info("Bot execution finished.")
