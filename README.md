# AI Board of Directors

A full-stack AI-powered Board of Directors application using LangGraph multi-agent architecture with a modern Streamlit frontend.

## Project Structure

```
ai_board/
├── backend/                    # Python/LangGraph Backend
│   ├── agents.py              # Agent nodes (Strategist, Financial, Risk, CEO)
│   ├── config.py               # LLM provider configuration
│   ├── graph.py                # StateGraph with supervisor routing
│   ├── main.py                 # Entry point with run_board_meeting()
│   ├── state.py                # TypedDict state with message reducers
│   ├── utils.py                # Formatting and utility functions
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                   # Streamlit Frontend
│   ├── app.py                  # Main Streamlit application
│   ├── config.py               # Frontend configuration
│   ├── requirements.txt
│   ├── components/
│   │   ├── sidebar.py          # LLM config sidebar
│   │   ├── chat_display.py    # Real-time debate display
│   │   └── decision_panel.py  # Decision summary
│   ├── utils/
│   │   └── backend_client.py   # Backend communication
│   └── README.md
│
└── README.md                   # This file
```

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Configure environment
export OPENAI_API_KEY=your_api_key

# Test the backend
python main.py
```

### Frontend Setup

```bash
cd frontend
pip install -r requirements.txt

# Run the frontend
streamlit run app.py
```

## Tech Stack

- **Backend:** Python, LangGraph, LangChain, OpenAI/Anthropic/Groq
- **Frontend:** Streamlit, Python, Requests

## Features

- 🎯 Multi-agent board meeting simulation
- 👔 Strategic, Financial, Risk, and CEO perspectives
- 💬 Real-time debate display with agent avatars
- 📊 Structured decision output with metrics
- 💾 Thread-based session persistence
- ⚙️ Multiple LLM provider support (OpenAI, Anthropic, Groq)
- 🌙 Professional dark theme UI