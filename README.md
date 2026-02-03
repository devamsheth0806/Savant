# 🩺 The Savant - AI-Powered Emergency Response Assistant

**The Savant** is an AI-powered emergency response assistant designed to guide untrained bystanders through life-saving medical interventions using TCCC (Tactical Combat Casualty Care) and AHA (American Heart Association) protocols.

## 🎯 Overview

Built with VocalBridge's conversational AI and LiveKit's real-time voice infrastructure, The Savant provides step-by-step verbal guidance for critical procedures like CPR, hemorrhage control, and airway management through an intuitive voice-first interface.

### Key Features
- 🎙️ **Real-time voice guidance** via VocalBridge AI
- 🌐 **Browser-based interface** with LiveKit WebRTC
- 📊 **Automated incident reporting** via Zapier MCP
- 💾 **Structured data logging** to Google Sheets
- 📧 **Email reports** to supervisors
- 💬 **Slack notifications** for team coordination

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- VocalBridge AI API Key
- (Optional) Zapier MCP Server for post-call automation

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "The Savant"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   VOCAL_BRIDGE_KEY=vb_your_api_key_here
   VOCAL_BRIDGE_URL=https://vocalbridgeai.com
   
   # Optional: For post-call automation
   ZAPIER_MCP_SERVER=http://localhost:3000
   ZAPIER_EMAIL_TO=supervisor@example.com
   ZAPIER_SHEETS_ID=your-google-sheet-id
   ZAPIER_SLACK_CHANNEL=#incidents
   ```

4. **Run the application**
   ```bash
   cd frontend
   streamlit run app.py
   ```

5. **Access the app**
   - Local: http://localhost:8501
   - Network: http://192.168.x.x:8501

## 📱 Mobile Access

For mobile microphone access, serve over HTTPS:
- Use ngrok: `ngrok http 8501`
- Deploy to Streamlit Cloud (automatic HTTPS)

## 🔧 Project Structure

```
The Savant/
├── frontend/
│   └── app.py                    # Main Streamlit web interface
├── backend/
│   ├── conversation_manager.py   # Core conversation orchestration
│   ├── voice_bridge_client.py    # VocalBridge/LiveKit integration
│   ├── audio_bridge.py           # TTS/audio utilities
│   ├── database_manager.py       # Patient data logging (TinyDB)
│   └── vision_processor.py       # Vision capabilities
├── data/
│   └── patient_logs.json         # Incident history
├── .env                          # Environment configuration
├── requirements.txt              # Python dependencies
└── README.md
```

## 🩺 Usage Workflow

### During Emergency
1. User opens app → clicks **"ACTIVATE VOICE LINK"**
2. Browser connects to VocalBridge agent via LiveKit
3. User speaks: *"He's not breathing!"*
4. **The Savant** responds: *"Start CPR. Center of chest. Push hard and fast."*
5. Conversation continues with step-by-step guidance
6. User clicks **"TERMINATE SESSION"** when emergency resolved

### Post-Call Processing (with Zapier MCP)
7. VocalBridge AI analyzes transcript with configured prompt
8. Extracts structured data: injuries, vitals, actions, timeline
9. Triggers Zapier MCP tools:
   - **Google Sheets**: Logs incident data
   - **Gmail**: Sends report to supervisor
   - **Slack**: Notifies team in #incidents channel

## 🔑 VocalBridge Configuration

### Agent Prompt
Configure in VocalBridge dashboard:

```
You are The Savant, an advanced medical AI who speaks only in English.
Your Goal: Guide untrained bystanders to save lives using TCCC and AHA protocols.

CORE BEHAVIORS:
1. VOICE FIRST: Do NOT assume anything. Get clarity.
2. BE DIRECT: Short, declarative sentences.
3. BE PRECISE: Medical terms + layman actions.

INTERACTION:
- Listen to user's description
- Issue ONE instruction at a time

EXAMPLE:
User: "He's not breathing!"
You: "Check pulse. Carotid artery. Ten seconds. Feel it?"
User: "No!"
You: "Start CPR. Center of chest. Push hard and fast."
```

### Post-Processing Prompt
For incident data extraction, add this to VocalBridge post-call configuration:

```
Extract emergency incident data as JSON:
{
  "incident_timestamp": "ISO 8601 datetime",
  "duration_seconds": int,
  "severity": "Critical|Serious|Moderate|Minor",
  "patient": {
    "injuries": [],
    "vitals": {"heart_rate": int, "blood_pressure": "string"},
  },
  "actions_taken": [],
  "equipment_used": [],
  "key_events": [{"time_offset_seconds": int, "event": "string"}],
  "summary": "brief summary",
  "hospital_handoff": "critical info for hospital"
}
```

## 🔗 Zapier MCP Integration

### Required Tools
1. **google_sheets_append_row** - Log incidents
2. **gmail_send_email** - Email reports
3. **slack_post_message** - Team notifications

### Google Sheets Setup
Create a sheet with columns:
| Timestamp | Duration | Severity | Injuries | Vitals | Actions | Equipment | Summary | Handoff |

Get Sheet ID from URL: `docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Code Style
- Black formatting
- Type hints where applicable

## 📄 License

[Add your license here]

## 👥 Contributors

[Add contributors]

## 🙏 Acknowledgments

- VocalBridge AI for conversational AI platform
- LiveKit for real-time voice infrastructure
- Streamlit for rapid UI development
- Zapier MCP for automation capabilities

---

**Emergency Contact**: For issues during active emergencies, always call 911 first. This tool is designed to assist, not replace, professional emergency services.
