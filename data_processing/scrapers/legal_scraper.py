#
# legal_scraper.py
#
import os
import requests
import fitz
import time

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
LANDING_PAGE_URL = "https://peraturan.bpk.go.id/Details/39162/uu-no-20-tahun-2008"
BASE_URL = "https://peraturan.bpk.go.id"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'raw_data')
OUTPUT_FILENAME = "uu_no_20_tahun_2008.txt"

# --- Functions ---

def get_pdf_link_with_selenium(url: str) -> str | None:
    """
    Uses Selenium to open a URL, waits for the specific download button
    (with an href attribute) to be clickable, and extracts the link.
    """
    print("[*] Initializing Selenium WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print(f"[*] Visiting landing page with Selenium: {url}")
        driver.get(url)
        
        print("[*] Waiting for the specific download link to become clickable...")
        wait = WebDriverWait(driver, 20)
        
        selector = "a.download-file[href]"
        download_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        
        print("[+] Specific download link element is now clickable!")
        
        pdf_url = download_element.get_attribute('href')
        
        if pdf_url:
            print(f"[+] Successfully extracted PDF link via Selenium: {pdf_url}")
            return pdf_url
        else:
            print("[!] Element was found, but it somehow still has no 'href' attribute.")
            return None
        
    except Exception as e:
        print(f"[!] An error occurred with Selenium: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            print("[*] Selenium WebDriver closed.")


def download_and_extract_text(pdf_url: str) -> str | None:
    """
    Downloads a PDF file from a URL and extracts all its text.
    """
    try:
        print(f"[*] Downloading PDF from: {pdf_url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        pdf_response = requests.get(pdf_url, headers=headers, timeout=45)
        pdf_response.raise_for_status()
        print("[+] PDF downloaded successfully.")

        print("[*] Parsing PDF and extracting text...")
        pdf_document = fitz.open(stream=pdf_response.content, filetype="pdf")
        
        full_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            full_text += page.get_text()
            
        print(f"[+] Text extracted from all {len(pdf_document)} pages.")
        return full_text

    except Exception as e:
        print(f"[!] An error occurred during PDF download or parsing: {e}")
        return None

def save_text_to_file(text: str, directory: str, filename: str):
    """
    Saves a given string of text to a file.
    """
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[+] Successfully saved data to: {file_path}")
    except IOError as e:
        print(f"[!] Error writing to file: {e}")

# --- Main Execution ---
def main():
    print("--- Starting Legal Data Scraper (v9 - Final URL Handling) ---")
    
    # 1. Use Selenium to get the PDF link (could be relative or absolute)
    pdf_url_from_selenium = get_pdf_link_with_selenium(LANDING_PAGE_URL)
    
    if pdf_url_from_selenium:
        # Check if the extracted URL is already a full URL.
        if pdf_url_from_selenium.startswith('http'):
            # If yes, use it directly.
            pdf_absolute_url = pdf_url_from_selenium
        else:
            # If no (it's a relative path like "/Download/..."), then construct the full URL.
            pdf_absolute_url = f"{BASE_URL}{pdf_url_from_selenium}"
        
        # 3. Download and extract text from the corrected URL
        extracted_text = download_and_extract_text(pdf_absolute_url)
        
        if extracted_text:
            # 4. Save the result
            save_text_to_file(extracted_text, OUTPUT_DIR, OUTPUT_FILENAME)
        else:
            print("[!] PDF text extraction failed.")
    else:
        print("[!] Failed to get PDF link. Stopping script.")
        
    print("--- Scraper Finished ---")

if __name__ == "__main__":
    main()