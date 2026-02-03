"""
THE SAVANT - First Responder AI System
Enhanced Frontend Application
"""
import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import threading
import asyncio

# Add parent directory to path for backend imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.conversation_manager import ConversationManager

# Page Configuration
st.set_page_config(
    page_title="The Savant // First Responder AI",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🩺"
)

# Enhanced CSS
st.markdown("""
<style>
    /* Main App Styling */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
        color: #00FF00;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Header Styling */
    .hud-header {
        color: #39FF14;
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, rgba(57,255,20,0.1) 0%, rgba(57,255,20,0.3) 50%, rgba(57,255,20,0.1) 100%);
        border: 2px solid #39FF14;
        border-radius: 10px;
        text-shadow: 0 0 20px #39FF14;
        margin-bottom: 30px;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 5px #39FF14, 0 0 10px #39FF14; }
        to { box-shadow: 0 0 10px #39FF14, 0 0 20px #39FF14, 0 0 30px #39FF14; }
    }
    
    /* Status Cards */
    .status-card {
        background: rgba(0, 50, 0, 0.3);
        border: 2px solid #39FF14;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.3);
    }
    
    /* Audio Visualizer Styling */
    .audio-container {
        background: rgba(0, 20, 0, 0.8);
        border: 3px solid #39FF14;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 25px rgba(57, 255, 20, 0.5);
    }
    
    /* Chat Message Styling */
    .stChatMessage {
        background: rgba(0, 30, 0, 0.5) !important;
        border-left: 4px solid #39FF14 !important;
    }
</style>
""", unsafe_allow_html=True)

# Singleton Manager
@st.cache_resource
def get_manager():
    return ConversationManager()

manager = get_manager()

def start_call():
    """Start voice bridge connection"""
    bridge = manager.voice_bridge
    
    if not getattr(bridge, 'active', False):
        st.session_state.call_active = True
        bridge.active = True
        
        def run_livekit(man):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(man.voice_bridge.connect_and_stream())
            except Exception as e:
                print(f"LiveKit Thread Error: {e}")

        # Start background thread for Python listener
        thread = threading.Thread(target=run_livekit, args=(manager,), daemon=True)
        thread.start()
    
    st.rerun()

def stop_call():
    """Stop voice bridge connection"""
    st.session_state.call_active = False
    if manager.voice_bridge:
        manager.voice_bridge.active = False
    st.rerun()

def main():
    # Header
    st.markdown('<div class="hud-header">🩺 THE SAVANT // FIRST RESPONDER AI</div>', unsafe_allow_html=True)
    
    # Sidebar Controls
    with st.sidebar:
        st.markdown("### 🎯 MISSION CONTROL")
        st.markdown("---")
        
        # Voice Bridge Status
        bridge = manager.voice_bridge
        backend_connected = bridge and bridge.room and bridge.room.connection_state
        
        # Control Buttons
        if not st.session_state.get('call_active', False):
            if st.button("📞 ACTIVATE VOICE LINK", type="primary", use_container_width=True):
                start_call()
        else:
            if st.button("⏹️ TERMINATE SESSION", type="secondary", use_container_width=True):
                stop_call()

        st.markdown("---")
        
        # System Status
        st.markdown("### 📡 SYSTEM STATUS")
        
        if backend_connected:
            st.success(f"🟢 **ONLINE**\n\nRoom: `{bridge.room.name}`")
            st.metric("Connection", "ACTIVE", "Stable")
        else:
            if st.session_state.get('call_active', False):
                st.warning("🟡 **INITIALIZING**\n\nEstablishing secure link...")
            else:
                st.error("🔴 **OFFLINE**\n\nSystem standby")
        
        st.markdown("---")
        
        # System Controls
        st.markdown("### ⚙️ CONTROLS")
        
        if st.button("🗑️ CLEAR LOGS", use_container_width=True):
            manager.history = []
            st.rerun()
        
        # System Info
        st.markdown("---")
        st.markdown("### ℹ️ SYSTEM INFO")
        st.caption("**Version:** 2.0")
        st.caption("**Engine:** VocalBridge AI")
        st.caption("**Status:** Operational")
    
    # Main Interface - Single Column Layout
    st.markdown("### 🎙️ VOICE INTERFACE")
    
    # Voice Bridge Client (Browser Audio)
    if st.session_state.get('call_active', False):
        token_data = manager.voice_bridge.get_token()
        
        if token_data:
            html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/livekit-client@2/dist/livekit-client.umd.min.js"></script>
                <style>
                    body {{ 
                        font-family: 'Courier New', monospace; 
                        text-align: center; 
                        padding: 30px; 
                        background: linear-gradient(135deg, #001400 0%, #002800 100%);
                        color: #39FF14;
                        margin: 0;
                    }}
                    #status {{ 
                        font-size: 22px; 
                        font-weight: bold; 
                        margin: 20px 0;
                        padding: 20px;
                        border: 3px solid #39FF14;
                        border-radius: 15px;
                        background: rgba(0, 50, 0, 0.5);
                        box-shadow: 0 0 25px rgba(57, 255, 20, 0.5);
                        animation: pulse 2s ease-in-out infinite;
                    }}
                    @keyframes pulse {{
                        0%, 100% {{ box-shadow: 0 0 15px rgba(57, 255, 20, 0.5); }}
                        50% {{ box-shadow: 0 0 30px rgba(57, 255, 20, 0.8); }}
                    }}
                    .connected {{ 
                        color: #00FF00;
                        text-shadow: 0 0 10px #00FF00;
                    }}
                    .error {{ 
                        color: #FF0000;
                        text-shadow: 0 0 10px #FF0000;
                    }}
                    .icon {{
                        font-size: 48px;
                        margin: 20px 0;
                        animation: rotate 3s linear infinite;
                    }}
                    @keyframes rotate {{
                        from {{ transform: rotate(0deg); }}
                        to {{ transform: rotate(360deg); }}
                    }}
                </style>
            </head>
            <body>
                <div class="icon">🎤</div>
                <div id="status">🔄 ESTABLISHING SECURE CONNECTION...</div>
                
                <script>
                    const statusEl = document.getElementById('status');
                    
                    async function startCall() {{
                        try {{
                            const room = new LivekitClient.Room({{
                                adaptiveStream: true,
                                dynacast: true,
                            }});
                            
                            // Handle incoming audio (agent voice)
                            room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {{
                                console.log('Track subscribed:', track.kind, participant.identity);
                                if (track.kind === LivekitClient.Track.Kind.Audio) {{
                                    const audioElement = track.attach();
                                    document.body.appendChild(audioElement);
                                    audioElement.play();
                                    console.log('🔊 Agent audio active');
                                }}
                            }});
                            
                            // Connect to room
                            await room.connect("{token_data['livekit_url']}", "{token_data['token']}");
                            statusEl.innerHTML = "🟢 VOICE LINK ACTIVE<br><small>Speak clearly into your microphone</small>";
                            statusEl.className = "connected";
                            
                            // Enable microphone
                            await room.localParticipant.setMicrophoneEnabled(true);
                            console.log('🎤 Microphone enabled');
                            
                        }} catch (error) {{
                            console.error('Connection error:', error);
                            statusEl.textContent = "❌ CONNECTION FAILED: " + error.message;
                            statusEl.className = "error";
                        }}
                    }}
                    
                    startCall();
                </script>
            </body>
            </html>
            """
            
            components.html(html_code, height=300)
        else:
            st.error("❌ Failed to fetch LiveKit token - Check API configuration")
    else:
        st.info("🔴 **Voice Link Offline**\n\nClick **ACTIVATE VOICE LINK** in the sidebar to begin")
    
    # Conversation History Section
    st.markdown("---")
    st.markdown("### 📋 CONVERSATION LOG")
    
    history = manager.history
    chat_container = st.container(height=400)
    
    with chat_container:
        if history:
            for msg in history:
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=role_icon):
                    st.markdown(msg["content"])
        else:
            if st.session_state.get('call_active', False):
                st.info("🟢 System Active - Conversation will appear here")
            else:
                st.info("🔴 Activate voice link to begin")

if __name__ == "__main__":
    main()
