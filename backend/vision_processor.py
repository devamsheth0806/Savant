import os
import base64
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - Savant Vision - %(message)s')

class VisionProcessor:
    def __init__(self):
        self.api_key = os.getenv('NIM_API_KEY')
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "meta/llama-3.2-90b-vision-instruct"
        
        if not self.api_key:
            logging.warning("NIM_API_KEY not found. Vision calls will fail.")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key or "dummy_key"
        )

    def analyze_injury(self, image_bytes):
        """
        Analyzes an injury image using NVIDIA NIM.
        Returns a structured JSON dictionary.
        """
        logging.info("Analyzing injury image...")
        
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = (
            "You are an AI Savant. Analyze this emergency image. "
            "Output strictly JSON: {'injury': '...', 'severity': 'CRITICAL', "
            "'visual_overlay': 'Arterial Bleed - Apply Tourniquet'}."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=1024,
                stream=False
            )
            
            content = response.choices[0].message.content
            # Clean up markdown code blocks if present
            if "```json" in content:
                content = content.replace("```json", "").replace("```", "")
            
            return json.loads(content)

        except Exception as e:
            logging.error(f"Vision analysis failed: {e}")
            # Fallback for demo purposes if API fails
            return {
                "injury_type": "Unknown",
                "severity": "Unknown",
                "visual_overlay_text": "Analysis Failed - Check Connection"
            }
