"""
THE SAVANT - Simplified Voice App
Based on standard LiveKit + Streamlit patterns
"""
import streamlit as st
import streamlit.components.v1 as components
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="THE SAVANT",
    page_icon="🎯",
    layout="wide"
)

def get_livekit_token():
    """Fetch LiveKit token from VocalBridge API"""
    api_key = os.getenv('VOCAL_BRIDGE_KEY')
    api_url = os.getenv('VOCAL_BRIDGE_URL', 'https://vocalbridgeai.com')
    
    try:
        response = requests.post(
            f"{api_url}/api/v1/token",  # Official endpoint from docs
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            json={"participant_name": "User"},  # Optional body parameter
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to get token: {e}")
        return None

def main():
    st.title("🎯 THE SAVANT")
    
    with st.sidebar:
        st.markdown("### SYSTEM STATUS")
        
        if st.button("📞 START CALL", type="primary"):
            st.session_state.call_active = True
            st.rerun()
            
        if st.session_state.get('call_active', False):
            if st.button("⏹️ END CALL", type="secondary"):
                st.session_state.call_active = False
                st.rerun()
    
    # Main Interface  
    if st.session_state.get('call_active', False):
        token_data = get_livekit_token()
        
        if token_data:
            # Embed LiveKit JS Client
            html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/livekit-client@2/dist/livekit-client.umd.min.js"></script>
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 20px; }}
                    #status {{ font-size: 18px; font-weight: bold; margin: 20px 0; }}
                    .connected {{ color: green; }}
                    .error {{ color: red; }}
                </style>
            </head>
            <body>
                <div id="status">Connecting...</div>
                <div id="transcript" style="margin-top: 20px; font-size: 14px;"></div>
                
                <script>
                    const statusEl = document.getElementById('status');
                    const transcriptEl = document.getElementById('transcript');
                    
                    async function startCall() {{
                        try {{
                            const room = new LivekitClient.Room({{
                                adaptiveStream: true,
                                dynacast: true,
                            }});
                            
                            // Handle incoming audio tracks (agent voice)
                            room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {{
                                console.log('Track subscribed:', track.kind);
                                if (track.kind === LivekitClient.Track.Kind.Audio) {{
                                    const audioElement = track.attach();
                                    document.body.appendChild(audioElement);
                                    audioElement.play();
                                    console.log('Agent audio playing');
                                }}
                            }});
                            
                            // Handle transcriptions
                            room.on(LivekitClient.RoomEvent.TranscriptionReceived, (transcription) => {{
                                console.log('Transcription:', transcription);
                                const text = transcription.segments.map(s => s.text).join(' ');
                                transcriptEl.innerHTML += `<p>${{text}}</p>`;
                            }});
                            
                            // Connect
                            await room.connect("{token_data['livekit_url']}", "{token_data['token']}");
                            statusEl.textContent = "🟢 Connected - Speak Now";
                            statusEl.className = "connected";
                            
                            // Enable microphone
                            await room.localParticipant.setMicrophoneEnabled(true);
                            
                        }} catch (error) {{
                            console.error('Connection error:', error);
                            statusEl.textContent = "❌ Connection Failed: " + error.message;
                            statusEl.className = "error";
                        }}
                    }}
                    
                    startCall();
                </script>
            </body>
            </html>
            """
            
            components.html(html_code, height=400)
        else:
            st.error("Failed to initialize call - check API key")
    else:
        st.info("Click **START CALL** in the sidebar to begin")

if __name__ == "__main__":
    main()
