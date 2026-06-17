# AI Board Frontend

A beautiful, modern Streamlit frontend for the AI-powered Board of Directors application.

## Features

- 🎨 Professional dark theme UI
- 💬 Real-time debate display with agent avatars
- 📊 Structured decision panel with metrics
- ⚙️ Configurable LLM providers (OpenAI, Anthropic, Groq)
- 💾 Meeting history and export functionality
- 🎯 Executive summary and action items

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp ../backend/.env.example .env
# Edit .env with your API keys

# Run the application
streamlit run app.py
```

## Project Structure

```
frontend/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration and settings
├── requirements.txt       # Python dependencies
├── components/
│   ├── __init__.py
│   ├── sidebar.py         # Configuration sidebar
│   ├── chat_display.py    # Debate display component
│   └── decision_panel.py  # Decision summary panel
└── utils/
    ├── __init__.py
    └── backend_client.py  # Backend communication client
```

## Configuration

The frontend connects to the backend in two modes:

1. **Import Mode** (default): Directly imports the backend Python module
2. **API Mode**: Communicates via HTTP REST API

### Environment Variables

```env
BACKEND_MODE=import        # or "api"
BACKEND_PATH=../backend    # Path to backend directory
BACKEND_API_URL=http://localhost:8000
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GROQ_API_KEY=your_key
```

## Tech Stack

- **Streamlit** - Web framework
- **Python** - Backend integration
- **LangGraph** - Multi-agent system (backend)
- **Requests/HTTPX** - API client