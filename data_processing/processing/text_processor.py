#
# text_processor.py (v6 - Enriched JSON Output)
#
# Description:
# This script reads a raw text file, chunks it by 'Pasal', and enriches
# each chunk with its corresponding 'BAB' (Chapter) ID and title.
# The output is a flat JSON list of article chunks.
#

import os
import json
import re

# --- Configuration ---
INPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'raw_data')
INPUT_FILENAME = "uu_no_20_tahun_2008.txt"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'processed_data')
OUTPUT_FILENAME = "uu_no_20_tahun_2008.json"
SOURCE_NAME = "uu_no_20_tahun_2008"

# --- Functions ---

def load_raw_text(filepath: str) -> str | None:
    """ Loads the raw text content from a file. """
    print(f"[*] Loading raw text from: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[!] Error reading file: {e}")
        return None

def process_text_to_chunks(text: str) -> list[dict]:
    """
    Chunks text by 'Pasal' and enriches each chunk with its parent 'BAB' info.
    """
    print("[*] Starting text processing to create enriched JSON...")
    
    all_pasal_chunks = []
    
    # Regex to find chapter headings (e.g., "BAB I")
    bab_pattern = r'(^\s*BAB\s+[IVXLCDM]+)'
    # Split the entire document by chapters
    document_parts = re.split(bab_pattern, text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Regex to find article headings (e.g., "Pasal 1")
    pasal_pattern = r'(^\s*Pasal\s+\d+\s*$)'
    
    # --- Process text BEFORE the first chapter (preamble) ---
    preamble_text = document_parts[0]
    pasal_parts_in_preamble = re.split(pasal_pattern, preamble_text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Handle any articles found before BAB I
    text_before_first_pasal = pasal_parts_in_preamble[0].strip()

    current_chapter_id = "N/A"
    current_chapter_title = "Preamble" # Default for text before the first chapter
    
    # First element is the preamble
    if text_before_first_pasal:
        all_pasal_chunks.append({
            "source": SOURCE_NAME,
            "chunk_type": "preamble",
            "chunk_id": "Preamble",
            "chapter_id": current_chapter_id,
            "chapter_title": current_chapter_title,
            "text": text_before_first_pasal
        })
 
    # if len(pasal_parts_in_preamble) > 1:
    #      for j in range(1, len(pasal_parts_in_preamble), 2):
    #         pasal_id = pasal_parts_in_preamble[j].strip()
    #         pasal_content = pasal_parts_in_preamble[j+1].strip()
    #         full_pasal_text = f"{pasal_id}\n{pasal_content}"
    #         if j == 1 and text_before_first_pasal:
    #              full_pasal_text = f"{text_before_first_pasal}\n\n{full_pasal_text}"

    #         all_pasal_chunks.append({
    #             "source": SOURCE_NAME,
    #             "chunk_type": "pasal",
    #             "chunk_id": pasal_id,
    #             "chapter_id": None, # No chapter for preamble articles
    #             "chapter_title": None,
    #             "text": full_pasal_text.strip()
    #         })

    # --- Process each chapter section ---
    current_bab_id = None
    current_bab_title = None
    
    for i in range(1, len(document_parts), 2):
        current_bab_id = document_parts[i].strip()
        bab_content_raw = document_parts[i+1]
        
        # Extract the chapter title
        content_lines = bab_content_raw.strip().split('\n')
        bab_title_parts = []
        text_after_title = []
        title_found = False
        
        for line in content_lines:
            stripped_line = line.strip()
            if not title_found and stripped_line and not stripped_line.lower().startswith(('pasal', 'bagian')):
                bab_title_parts.append(stripped_line)
            else:
                title_found = True
                text_after_title.append(line)
        current_bab_title = " ".join(bab_title_parts)

        # Split the content of this chapter by articles
        pasal_text_block = "\n".join(text_after_title)
        pasal_parts = re.split(pasal_pattern, pasal_text_block, flags=re.MULTILINE | re.IGNORECASE)
        
        text_before_first_pasal_in_bab = pasal_parts[0].strip()
        
        for j in range(1, len(pasal_parts), 2):
            pasal_id = pasal_parts[j].strip()
            pasal_content = pasal_parts[j+1].strip()
            
            full_pasal_text = f"{pasal_id}\n{pasal_content}"
            if j == 1 and text_before_first_pasal_in_bab:
                full_pasal_text = f"{text_before_first_pasal_in_bab}\n\n{full_pasal_text}"

            # Append the enriched article chunk
            all_pasal_chunks.append({
                "source": SOURCE_NAME,
                "chunk_type": "pasal",
                "chunk_id": pasal_id,
                "chapter_id": current_bab_id,
                "chapter_title": current_bab_title,
                "text": full_pasal_text.strip()
            })

    print(f"[+] Successfully created {len(all_pasal_chunks)} enriched pasal chunks.")
    return all_pasal_chunks


def save_chunks_to_json(chunks: list, directory: str, filename: str):
    """ Saves a list of chunks to a JSON file. """
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"[+] Successfully saved structured data to: {file_path}")
    except Exception as e:
        print(f"[!] An error occurred while saving to JSON: {e}")

# --- Main Execution ---
def main():
    print("--- Starting Text Processor ---")
    input_filepath = os.path.join(INPUT_DIR, INPUT_FILENAME)
    
    raw_text = load_raw_text(input_filepath)
    
    if raw_text:
        chunks = process_text_to_chunks(raw_text)
        
        if chunks:
            save_chunks_to_json(chunks, OUTPUT_DIR, OUTPUT_FILENAME)
        else:
            print("[!] No chunks were created from the text.")
    else:
        print("[!] Processing failed because raw text could not be loaded.")
        
    print("--- Text Processor Finished ---")

if __name__ == "__main__":
    main()