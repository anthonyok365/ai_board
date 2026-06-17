# AI Board Frontend

A beautiful, modern Streamlit frontend for the AI-powered Board of Directors application.

## Features

- 🎨 Professional dark theme UI
- 💬 Real-time debate display with agent avatars
- 📊 Structured decision panel with metrics
- ⚙️ Configurable LLM providers (OpenAI, Anthropic, Groq)
- 💾 Meeting history and export functionality
- 🎯 Executive summary and action items

## Quick Start (Local Development)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment to Streamlit Cloud

### 1. Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select repository: `anthonyok365/ai_board`
4. Set **Main file path:** `frontend/app.py`
5. Click **Advanced settings** → **Secrets** and add:
   - `OPENAI_API_KEY` = your key
   - `ANTHROPIC_API_KEY` = your key (optional)
   - `GROQ_API_KEY` = your key (optional)

### 2. Deploy

Click **Deploy!** - your app will be live at `https://your-app-name.streamlit.app`

## Project Structure

```
frontend/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration and settings
├── requirements.txt            # Python dependencies
├── .streamlit/
│   ├── config.toml             # Streamlit configuration
│   └── secrets.toml            # Secrets template
├── components/
│   ├── sidebar.py              # Configuration sidebar
│   ├── chat_display.py         # Debate display component
│   └── decision_panel.py       # Decision summary panel
└── client/
    └── backend_client.py       # Backend communication client
```

## Tech Stack

- **Streamlit** - Web framework
- **Python** - Backend integration
- **LangGraph** - Multi-agent system (backend)