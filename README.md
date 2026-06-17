# AI Board of Directors

A full-stack application featuring an AI-powered Board of Directors using LangGraph multi-agent architecture.

## Project Structure

```
ai_board/
├── backend/           # Python/LangGraph backend
│   ├── agents.py      # Agent nodes (Strategist, Financial, Risk, CEO)
│   ├── config.py      # LLM provider configuration
│   ├── graph.py       # StateGraph with supervisor routing
│   ├── main.py        # Entry point with run_board_meeting()
│   ├── state.py       # TypedDict state with message reducers
│   ├── utils.py       # Formatting and utility functions
│   ├── requirements.txt
│   └── README.md
│
├── frontend/          # React/Vue frontend (coming soon)
│   └── README.md
│
└── README.md          # This file
```

## Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Configure environment variables
export OPENAI_API_KEY=your_api_key

# Run a board meeting
python main.py
```

## Tech Stack

- **Backend:** Python, LangGraph, LangChain, OpenAI/Anthropic/Groq
- **Frontend:** React/Vue (to be implemented)

## Features

- Multi-agent board meeting simulation
- Strategic, Financial, Risk, and CEO perspectives
- Thread-based session persistence
- Structured decision output