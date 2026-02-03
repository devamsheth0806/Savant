import os
import io
import wave
import pyttsx3
import logging

class BackendAudioBridge:
    def __init__(self):
        # Initialize engine
        # Note: pyttsx3 initialization might fail in some headless environments without audio drivers
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 160) # Speed
            self.engine.setProperty('volume', 1.0)
            
            # Select a voice (Preferably Windows built-in David or Zira)
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
        except Exception as e:
            logging.error(f"Failed to init pyttsx3: {e}")
            self.engine = None

    def generate_pcm(self, text):
        """
        Generates 16-bit 48kHz PCM audio bytes from text using pyttsx3 (SAPI5).
        """
        if not text or not self.engine:
            return None
            
        try:
            # Save to temporary WAV file
            temp_file = "temp_output.wav"
            # pyttsx3 save_to_file runs in the event loop.
            # We must runAndWait() to process it.
            self.engine.save_to_file(text, temp_file)
            self.engine.runAndWait()
            
            # Read WAV bytes
            pcm_data = None
            if os.path.exists(temp_file):
                with wave.open(temp_file, 'rb') as wf:
                    # LiveKit expects 48kHz usually, but SAPI5 might output 22k or 44k.
                    # We send what we have. If LiveKit negotiates Opus it handles resampling?
                    # Or we might need to resample.
                    # For now, let's just read frames.
                    pcm_data = wf.readframes(wf.getnframes())
                    
                    # Log params
                    channels = wf.getnchannels()
                    rate = wf.getframerate()
                    width = wf.getsampwidth() 
                    logging.info(f"Generated Audio: {rate}Hz, {channels}ch, {width}bytes width")

                # Clean up
                os.remove(temp_file)
            
            return pcm_data
        except Exception as e:
            logging.error(f"TTS Conversion Error: {e}")
            return None
