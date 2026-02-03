import os
import json
import requests
import logging
from io import BytesIO
from pypdf import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - Savant DataPipeline - %(message)s')

PROTOCOL_URLS = {
    "TCCC_2024": "https://learning-media.allogy.com/api/v1/pdf/f4cf1d4e-3191-443a-befc-415838fb04f2/contents",
    "AHA_CPR_2025": "https://cpr.heart.org/-/media/CPR-Files/2025-documents-for-cpr-heart-edits-posting/Resuscitation-Science/252500_Hghlghts_2025ECCGuidelines.pdf?sc_lang=en",
    "WMS_ALTITUDE": "http://www.wildmedcenter.com/uploads/5/9/8/2/5982510/wms_altitude.pdf"
}

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "savant_protocols.json")

def download_pdf(url: str) -> BytesIO:
    """Downloads a PDF from a URL into memory."""
    try:
        logging.info(f"Downloading protocol from: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return None

def extract_text_from_pdf(pdf_stream: BytesIO) -> str:
    """Extracts raw text from a PDF stream."""
    if not pdf_stream:
        return ""
    try:
        reader = PdfReader(pdf_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logging.error(f"Failed to extract text: {e}")
        return ""

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def process_text_into_protocols(raw_text: str) -> dict:
    """
    Uses an LLM (NVIDIA Nemotron via OpenAI client) to extract a decision tree from raw text.
    Processes text in chunks to handle large documents.
    """
    logging.info("Processing extracted text into decision tree structures using LLM...")
    
    api_key = os.getenv('NIM_API_KEY')
    if not api_key:
        logging.warning("NIM_API_KEY not found. Using generic placeholder data.")
        return get_placeholder_data()

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

    CHUNK_SIZE = 15000
    overlap = 500
    chunks = [raw_text[i:i+CHUNK_SIZE] for i in range(0, len(raw_text), CHUNK_SIZE - overlap)]
    
    all_protocols = []
    
    logging.info(f"Split text into {len(chunks)} chunks for processing.")

    prompt = """
    You are an expert medical protocol extractor. Your task is to analyze the provided medical guidelines and extract emergency response protocols into a strict JSON format.
    
    The Output JSON must follow this schema:
    {
      "protocols": [
        {
          "id": "string (unique id, e.g., hemorrhage, cpr)",
          "name": "string (Human readable name)",
          "keywords": ["list", "of", "relevant", "keywords"],
          "tree": {
            "step_id": {
              "voice": "The exact voice instruction to give.",
              "visual_mode": boolean (true if visual overlay is needed),
              "options": {"user_reply_intent": "next_step_id"},
              "next": "next_step_id (if no options)"
            }
          }
        }
      ]
    }

    Extract protocols for: Massive Hemorrhage, CPR, and Airway management if present.
    If no relevant protocols are found in this chunk, return {"protocols": []}.
    Keep instructions direct and imperative (Dr. Shaun Murphy persona).
    """

    for i, chunk in enumerate(chunks):
        logging.info(f"Processing chunk {i+1}/{len(chunks)}...")
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-nano-30b-a3b",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Extract protocols from this text chunk:\n\n{chunk}"}
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=4096,
                stream=False
            )
            
            content = response.choices[0].message.content
            # Clean up markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            chunk_data = json.loads(content)
            if "protocols" in chunk_data and isinstance(chunk_data["protocols"], list):
                all_protocols.extend(chunk_data["protocols"])
            
        except Exception as e:
            logging.error(f"LLM Extraction failed for chunk {i+1}: {e}")
            continue

    if not all_protocols:
        logging.warning("No protocols extracted from any chunk. Using placeholder.")
        return get_placeholder_data()

    # Deduplicate protocols by ID (simple merge strategy)
    unique_protocols = {}
    for p in all_protocols:
        if "id" in p:
            unique_protocols[p["id"]] = p
            
    return {"protocols": list(unique_protocols.values())}

def get_placeholder_data():
    """Fallback data if LLM fails or no key."""
    return {
        "protocols": [
            {
                "id": "hemorrhage",
                "name": "Hemorrhage Control",
                "keywords": ["bleeding", "blood", "leg", "hemorrhage", "arterial"],
                "tree": {
                    "step_1": {
                        "voice": "Is blood spurting from the wound?",
                        "options": {
                            "yes": "step_tourniquet",
                            "no": "step_pressure"
                        }
                    },
                    "step_tourniquet": {
                        "voice": "Place tourniquet 2 to 3 inches above the wound. Tighten until bleeding stops.",
                        "visual_mode": True,
                        "next": "step_check_time"
                    },
                     "step_check_time": {
                         "voice": "Note the application time on the tourniquet.",
                         "visual_mode": False
                     },
                     "step_pressure": {
                        "voice": "Apply direct, steady pressure to the bleeding site.",
                        "visual_mode": True
                    }
                }
            }
        ]
    }

def main():
    all_text = ""
    
    # 1. Download and Extract
    # Note: We attempt download, but if it fails (offline/link rot), 
    # we proceed with empty text to ensure the JSON structure is generated for the demo.
    for name, url in PROTOCOL_URLS.items():
        pdf_stream = download_pdf(url)
        if pdf_stream:
            text = extract_text_from_pdf(pdf_stream)
            all_text += text
            logging.info(f"Extracted {len(text)} characters from {name}")
        else:
            logging.warning(f"Skipping download for {name}, proceeding with synthetic generation.")

    # 2. Process into Decision Tree
    # Even if download fails, we generate the critical protocol JSON for the agent to function.
    savant_protocols = process_text_into_protocols(all_text)

    # 3. Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(savant_protocols, f, indent=2)
    
    logging.info(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
