import logging
from backend.database_manager import DatabaseManager
from backend.vision_processor import VisionProcessor
from backend.voice_bridge_client import VoiceBridgeClient
from backend.audio_bridge import BackendAudioBridge
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - Savant Manager - %(message)s')

class ConversationManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.vision = VisionProcessor()
        self.voice_bridge = VoiceBridgeClient()
        self.audio = BackendAudioBridge()
        self.active_protocol = None
        self.current_step_id = None
        self.conversation_active = False
        self.history = [] # List of {"role": "user/assistant", "content": "..."}
        
        # Link Voice Bridge Input (Text Data) to Process Logic
        self.voice_bridge.set_on_message(self.process_input)
        logging.info(f"✓ ConversationManager initialized. Callback wired to process_input.")



    async def _speak_and_return(self, text):
        """Helper to stream audio and return text."""
        # Append to History
        self.history.append({"role": "assistant", "content": text})

        if self.voice_bridge.source:
            pcm = self.audio.generate_pcm(text)
            if pcm:
                await self.voice_bridge.send_audio(pcm)
        return text

    async def start_conversation(self):
        """Initializes the conversation state."""
        self.conversation_active = True
        self.active_protocol = None
        self.current_step_id = None
        return await self._speak_and_return("Savant System Online. Monitoring vitals. Describe the emergency.")

    async def process_input(self, user_text=None, image_bytes=None):
        """
        Main logic loop.
        - Analyze image (if present) -> Convert to text.
        - Combine with User Voice.
        - Search Protocol / Next Step -> Return Response.
        """
        logging.info(f"PROCESS_INPUT CALLED. Text: {user_text}, Image: {bool(image_bytes)}")
        
        # Append to history
        if user_text:
            self.history.append({"role": "user", "content": user_text})
            logging.info(f"Appended User Input. History Size: {len(self.history)}")
        elif image_bytes:
             self.history.append({"role": "user", "content": "📸 [Image Analysis]"})

        visual_context = ""
        
        # 1. Analyze Image if provided (DISABLED IN ECHO MODE)
        if image_bytes and self.vision:
            logging.info("Processing visual input...")
            analysis = self.vision.analyze_injury(image_bytes)
            injury = analysis.get("injury", "Unknown")
            severity = analysis.get("severity", "Unknown")
            visual_context = f"[Visual Info: Found {injury}, Severity: {severity}]"
            
            # Log to DB
            if self.db:
                self.db.log_patient_state(
                    heart_rate="--", 
                    injury_detected=injury, 
                    actions_taken=f"Visual Analysis: {severity}"
                )

        # 2. Combine Inputs
        final_input = user_text if user_text else ""
        if visual_context:
            final_input += f" {visual_context}"
        
        if not final_input:
            return await self._speak_and_return("Awaiting input.")

        logging.info(f"Processing combined input: {final_input}")
        
        # Send Context to Vocal Bridge Agent (LiveKit Data)
        # Note: In a real async app, we would await this. 
        # Here we check if the bridge is active (headless mode) or just log the intent.
        if self.voice_bridge.room:
             # This requires an event loop. 
             # For this prototype, we assume the Voice Bridge is running in parallel or we log the intent.
             logging.info(f"Sending context to LiveKit: {final_input}")
             # task = asyncio.create_task(self.voice_bridge.publish_context(final_input))
             await self.voice_bridge.publish_context(final_input)
        else:
             logging.warning("Voice Bridge not connected. Context not sent to remote agent.")

        # SIMPLIFIED ECHO MODE - RAG DISABLED FOR TESTING
        logging.info(f"✓ Echo Mode: Responding to '{final_input}'")
        return await self._speak_and_return(f"I heard you say: {final_input}")
