#
# detik_solusiukm_scraper.py
#
# Description:
# This script scrapes UMKM-related articles from https://finance.detik.com/solusiukm
# to build a knowledge base for an AI project. It collects the URL, title, and content
# of each article and saves them into a structured JSON file.
#

import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- Configuration ---
CATEGORY_URL = "https://finance.detik.com/solusiukm"
ARTICLE_LIMIT = 50  # Set to 50 for your knowledge base
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'raw_data')
OUTPUT_FILENAME = "detik_solusiukm_articles.json"

# --- Functions ---

def get_article_links(driver, url: str, limit: int) -> list[str]:
    """Navigates to the solusiukm page and scrapes article links."""
    print(f"[*] Visiting category page to find article links: {url}")
    driver.get(url)
    links = []
    try:
        wait = WebDriverWait(driver, 20)

        # Handle potential cookie consent pop-up
        try:
            print("[*] Checking for cookie consent button...")
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "cookie__button--accept"))
            )
            print("[*] Cookie consent pop-up found, closing it...")
            cookie_button.click()
            time.sleep(1)
        except Exception:
            print("[*] No cookie consent pop-up found, continuing...")

        # Scroll to load more articles (Detik often uses infinite scroll)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(links) < limit:
            # Find article links
            article_elements = driver.find_elements(By.CSS_SELECTOR, "article a")
            for elem in article_elements:
                if len(links) >= limit:
                    break
                link = elem.get_attribute('href')
                if link and "detik.com" in link and "/solusiukm/d-" in link and link not in links:
                    links.append(link)

            # Scroll down to load more
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for new content to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # No more content to load
                break
            last_height = new_height

        print(f"[+] Found {len(links)} unique article links.")
        return links
    except Exception as e:
        print(f"[!] Error finding article links: {e}")
        return []

def scrape_article_content(driver, url: str) -> dict | None:
    """Visits a single article page and scrapes its title and content."""
    print(f"    - Scraping content from: {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # Wait for the main content area to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "detail__body-text")))

        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract title
        title_tag = soup.find('h1', class_='detail__title')
        title = title_tag.get_text(strip=True) if title_tag else "Title not found"

        # Extract content
        content_div = soup.find('div', class_='detail__body-text')
        if not content_div:
            print(f"    - [!] Content div not found for {url}")
            return None

        # Remove unwanted elements
        for unwanted in content_div.find_all(['div', 'script', 'style', 'figure']):
            unwanted.decompose()

        content = content_div.get_text(separator='\n', strip=True)

        return {"url": url, "title": title, "content": content}

    except Exception as e:
        print(f"    - [!] Error scraping article content from {url}: {e}")
        return None

def save_to_json(data: list, directory: str, filename: str):
    """Saves the scraped data to a JSON file."""
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n[+] Successfully saved {len(data)} articles to: {file_path}")
    except Exception as e:
        print(f"[!] Error saving to JSON: {e}")

# --- Main Execution ---

def main():
    print("--- Starting Detik SolusiUKM Article Scraper ---")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = None
    scraped_articles = []
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Step 1: Get article links
        article_links = get_article_links(driver, CATEGORY_URL, ARTICLE_LIMIT)

        # Step 2: Scrape content for each article
        if article_links:
            print(f"[*] Starting to scrape content for {len(article_links)} articles...")
            for link in article_links:
                article_data = scrape_article_content(driver, link)
                if article_data:
                    scraped_articles.append(article_data)
                time.sleep(1)  # Be polite to the server

        # Step 3: Save to JSON
        if scraped_articles:
            save_to_json(scraped_articles, OUTPUT_DIR, OUTPUT_FILENAME)
        else:
            print("[!] No articles were scraped successfully.")

    except Exception as e:
        print(f"[!] A critical error occurred in the main process: {e}")
    finally:
        if driver:
            driver.quit()
            print("[*] Selenium WebDriver closed.")

    print("--- Scraper Finished ---")

if __name__ == "__main__":
    main()