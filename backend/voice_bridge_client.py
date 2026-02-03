import asyncio
import requests
import os
import logging
import json
import sounddevice as sd
import numpy as np
from livekit import rtc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - Savant VoiceBridge - %(message)s')

class VoiceBridgeClient:
    def __init__(self):
        self.api_url = "https://vocalbridgeai.com/api/v1/token"
        self.api_key = os.getenv('VOCAL_BRIDGE_KEY')
        self.room = None
        self.source = None
        self.track = None
        self.on_message_callback = None # Function(text)
        self.disconnect_signal = None # Future for signalling reconnect
        self._audio_stream_task = None
        self._mic_task = None

    def set_on_message(self, callback):
        self.on_message_callback = callback
    
    def get_token(self):
        """Fetches a LiveKit token from VocalBridge API."""
        if not self.api_key:
            logging.error("VOCAL_BRIDGE_KEY is missing.")
            return None
            
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # self.api_url already includes /api/v1/token
            response = requests.post(
                self.api_url,
                headers=headers,
                json={"participant_name": "TheSavant"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to get token: {e}")
            return None

    def _on_data_received(self, data: rtc.DataPacket):
        """Has incoming data packets."""
        try:
            # Handle transcription packets explicitly
            if data.topic == "lk.transcription":
                try:
                    text = data.data.decode('utf-8')
                    # Could be JSON or raw text depending on agent implementation
                    if text.startswith('{') and 'text' in text:
                        import json
                        obj = json.loads(text)
                        text = obj.get('text', text)
                    
                    self._process_text_message(text, "transcription_packet")
                    return
                except:
                    pass

            # Accept ALL topics for robustness (fallback)
            text = data.data.decode('utf-8')
            self._process_text_message(text, data.topic)
            
        except Exception as e:
            logging.warning(f"Failed to decode msg: {e}")

    def _process_text_message(self, text, source):
        if text and text.strip():
            logging.info(f"Message from {source}: {text}")
            if self.on_message_callback:
                asyncio.create_task(self._safe_callback_run(text))

    async def _safe_callback_run(self, text):
        try:
            await self.on_message_callback(text)
        except Exception as e:
            logging.error(f"Callback Execution Failed: {e}", exc_info=True)

    def _on_track_subscribed(self, track, publication, participant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logging.info(f"Subscribed to audio track from {participant.identity}")

    def _on_transcription_received(self, transcription, participant, publication):
        """Handles legacy transcription events."""
        try:
            # Ignore agent's own transcriptions (prevent echo loop)
            if participant and "agent-" in participant.identity:
                return
            
            participant_name = participant.identity if participant else 'Unknown'
            
            # transcription is already a list of segment objects
            if isinstance(transcription, list):
                full_text = " ".join([seg.text for seg in transcription if hasattr(seg, 'text')])
            else:
                # Fallback if it's a different structure
                full_text = str(transcription)
            
            if full_text.strip():
                logging.info(f"Transcription: {full_text}")
                if self.on_message_callback:
                    asyncio.create_task(self._safe_callback_run(full_text))
        except Exception as e:
            logging.warning(f"Failed to process transcription: {e}")

    async def _mic_capture_loop(self, source):
        """Captures mic via sounddevice and pushes to LiveKit source"""
        SAMPLE_RATE = 48000
        CHANNELS = 1
        
        logging.info("Starting Microphone Capture...")
        
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def callback(indata, frames, time, status):
            if status:
                print(status)
            loop.call_soon_threadsafe(queue.put_nowait, indata.copy())

        try:
            # Open Input Stream
            # High blocksize reduces CPU interruptions. 'low' latency is usually fine but 'high' is safer vs overflow.
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', 
                                callback=callback, blocksize=2048, latency='high'):
                 while True:
                    indata = await queue.get()
                    # Convert raw bytes to frame
                    # indata is numpy array (frames, channels) of int16
                    # tobytes() gives raw PCM
                    frame_data = indata.tobytes()
                    
                    frame = rtc.AudioFrame(
                        data=frame_data,
                        sample_rate=SAMPLE_RATE,
                        num_channels=CHANNELS,
                        samples_per_channel=len(indata) # indata length is frames
                    )
                    await source.capture_frame(frame)
        except asyncio.CancelledError:
            logging.info("Mic loop cancelled")
        except Exception as e:
            logging.error(f"Mic Error: {e}")

    async def _audio_play_loop(self, audio_stream):
        """Reads from LiveKit audio stream and plays via sounddevice"""
        SAMPLE_RATE = 48000
        CHANNELS = 1
        
        logging.info("Starting Speaker Output...")
        
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()
        
        def callback(outdata, frames, time, status):
            if status:
                print(status)
            try:
                data = queue.get_nowait()
                # Ensure size matches
                if len(data) < len(outdata):
                    outdata[:len(data)] = data
                    outdata[len(data):] = b'\x00' * (len(outdata) - len(data))
                else:
                    outdata[:] = data[:len(outdata)]
            except asyncio.QueueEmpty:
                outdata.fill(0)
        
        # Simpler approach: Blocking write in async executor or just simple stream write
        # Logic: LiveKit stream yields frames. We write to stream.
        
        try:
            with sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16') as stream:
                async for event in audio_stream:
                    # audio_stream yields AudioFrameEvent, which contains the frame
                    frame = event.frame
                    
                    # Convert from frame (AudioFrame)
                    # frame.data returns memoryview/bytes
                    data = np.frombuffer(frame.data, dtype=np.int16)
                    stream.write(data)
        except asyncio.CancelledError:
            logging.info("Audio play loop cancelled")
        except Exception as e:
            logging.error(f"Speaker Error: {e}")

    async def close(self):
        """Gracefully disconnects and cleans up resources."""
        logging.info("Closing VoiceBridge connection...")
        if self._mic_task:
            self._mic_task.cancel()
        if self._audio_stream_task:
            self._audio_stream_task.cancel()
        
        if self.room:
            await self.room.disconnect()
            logging.info("Room disconnected.")
            
        self.room = None
        self.source = None
        self.track = None



    async def _mic_capture_loop(self, source):
        """Disabled for Hybrid Mode"""
        pass

    async def _audio_play_loop(self, audio_stream):
        """Disabled for Hybrid Mode"""
        # Just consume stream without playing to avoid buffer buildup
        async for event in audio_stream:
             pass

    async def connect_and_stream(self):
        """Connects and maintains call (Passive/Data Mode)."""
        try:
            token_data = self.get_token()
            if not token_data: return

            logging.info(f"Connecting to room: {token_data.get('room_name')}")
            
            self.room = rtc.Room()

            # Set up event handlers
            @self.room.on("track_subscribed")
            def on_track_subscribed(track, publication, participant):
                if track.kind == rtc.TrackKind.KIND_AUDIO:
                    logging.info("Agent audio connected! (Passive listening)")
                    # We must subscribe/consume to keep connection healthy, but not play
                    audio_stream = rtc.AudioStream(track)
                    self._audio_stream_task = asyncio.create_task(self._audio_play_loop(audio_stream))

            @self.room.on("disconnected")
            def on_disconnected():
                logging.info("Disconnected from room")

            @self.room.on("data_received")
            def on_data_received(data: rtc.DataPacket):
                self._on_data_received(data)

            @self.room.on("transcription_received")
            def on_transcription_received(transcription, participant, publication):
                self._on_transcription_received(transcription, participant, publication)

            # Connect (PASSIVE - No Audio Publish)
            await self.room.connect(token_data["livekit_url"], token_data["token"])
            logging.info(f"Connected: {self.room.name}")

            # Note: We do NOT publish mic here. The Browser Client handles that.
            
            # Keep alive until room is closed or stopped active
            self.active = True
            while self.active and self.room and self.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Connection Error: {e}", exc_info=True)
        finally:
            await self.close()

    async def reconnect(self): pass

    async def send_audio(self, p): pass

    async def publish_context(self, text_context):
        """
        Publishes text context (e.g., visual analysis) to the room as a data packet.
        """
        if not self.room or not self.room.local_participant:
            logging.warning("Room not connected. Cannot publish context.")
            return

        try:
            data = text_context.encode('utf-8')
            await self.room.local_participant.publish_data(data, reliable=True)
            logging.info(f"Published context: {text_context[:50]}...")
        except Exception as e:
            logging.error(f"Failed to publish data: {e}")

if __name__ == "__main__":
    client = VoiceBridgeClient()
    asyncio.run(client.connect_and_stream())
