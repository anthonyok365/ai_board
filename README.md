# AI Board of Directors Backend

A production-grade multi-agent system built with LangGraph that simulates a professional Board of Directors for business decision-making.

## Overview

This backend implements an AI-powered board meeting system where specialized AI agents (Strategist, Financial Analyst, Risk Officer, and CEO) collaboratively analyze business decisions and produce structured recommendations.

### Key Features

- **Multi-Agent Architecture**: Specialized agents with distinct roles and expertise
- **Supervisor Orchestration**: Intelligent routing based on conversation state
- **Thread-Based Sessions**: Persistent conversations with MemorySaver checkpointing
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, and Groq
- **Human-in-the-Loop Ready**: Designed for human oversight and intervention
- **Production-Ready**: Comprehensive type hints, error handling, and logging

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         supervisor                          │
│                   (Board Chair - routing)                   │
└─────────┬───────────┬───────────┬───────────┬──────────────┘
          │           │           │           │
          ▼           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │strategist│ │financial │ │   risk   │ │   ceo    │
    │(Strategy)│ │(Finance) │ │  (Risk)  │ │(CEO/Exec)│
    └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │            │
         └────────────┴────────────┴────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │final_decision │
                 │(Board Summary)│
                 └───────┬───────┘
                         │
                         ▼
                        END
```

## Installation

```bash
# Clone or navigate to the project directory
cd ai-board-backend

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with your API keys:

```env
# LLM Provider Configuration
LLM_PROVIDER=openai  # Options: openai, anthropic, groq

# API Keys (at least one required based on provider)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GROQ_API_KEY=your_groq_api_key

# Optional: Use premium models (more expensive but more capable)
USE_PREMIUM_MODELS=false
```

### Provider Defaults

| Provider   | Default Model           | Premium Model        |
|------------|-------------------------|----------------------|
| OpenAI     | gpt-4o-mini             | gpt-4o               |
| Anthropic  | claude-sonnet-4         | claude-opus-4        |
| Groq       | llama-3.3-70b-versatile | llama-3.3-70b-versatile |

## Usage

### Basic Usage

```python
from main import run_board_meeting

# Run a board meeting
result = run_board_meeting(
    query="Should we invest $800k in expanding our AI product line next quarter?",
    thread_id="meeting_20260101_120000"
)

if result["success"]:
    print(result["decision"])
else:
    print(f"Error: {result['error']}")
```

### With Custom Configuration

```python
from main import run_board_meeting
from config import Config, set_provider

# Use premium models
set_provider("openai", use_premium=True)

# Run meeting
result = run_board_meeting(
    query="Should we expand into the European market?",
    thread_id="europe_expansion_q1",
    use_premium=True  # Uses gpt-4o instead of gpt-4o-mini
)
```

### Continue an Existing Meeting

```python
from main import continue_meeting, get_meeting_history

# Add additional input to an existing meeting
result = continue_meeting(
    thread_id="existing_meeting_id",
    additional_query="What are the tax implications of this expansion?"
)

# Get meeting history
history = get_meeting_history("existing_meeting_id")
```

### Retrieve Board Decision Sections

```python
from main import run_board_meeting
from utils import extract_sections_from_decision

result = run_board_meeting(query="Should we launch a new product line?")

if result["decision"]:
    sections = extract_sections_from_decision(result["decision"])
    
    print("Executive Summary:")
    print(sections.get("EXECUTIVE SUMMARY"))
    
    print("\nKey Recommendations:")
    print(sections.get("KEY RECOMMENDATIONS"))
```

## Project Structure

```
ai-board-backend/
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── config.py          # Configuration and LLM setup
├── state.py           # LangGraph state definitions
├── agents.py          # Agent node implementations
├── graph.py           # StateGraph construction
├── main.py            # Entry point and API
└── utils.py           # Utility functions
```

### File Descriptions

| File | Description |
|------|-------------|
| `config.py` | Environment configuration, LLM provider setup, model selection |
| `state.py` | AgentState TypedDict with message reducers, state utilities |
| `agents.py` | Agent node functions (strategist, financial, risk, ceo, supervisor) |
| `graph.py` | StateGraph construction, conditional routing, checkpointer setup |
| `main.py` | Main API (`run_board_meeting`), session management, examples |
| `utils.py` | Output formatting, validation, logging, export utilities |

## Board Members

### Strategist
- **Role**: Chief Strategy Officer
- **Focus**: Growth strategy, market expansion, innovation, competitive advantage
- **Output**: Strategic opportunities, market rationale, implementation approach

### Financial Analyst
- **Role**: Chief Financial Officer
- **Focus**: Revenue modeling, ROI analysis, cost structure, financial viability
- **Output**: Investment analysis, revenue projections, financial recommendations

### Risk Officer
- **Role**: Chief Risk Officer
- **Focus**: Risk identification, compliance, mitigation strategies, scenario planning
- **Output**: Risk assessment, contingency plans, go/no-go recommendations

### CEO
- **Role**: Chief Executive Officer
- **Focus**: Synthesis, decision-making, execution planning, organizational alignment
- **Output**: Executive assessment, clear recommendations, next steps

### Supervisor (Board Chair)
- **Role**: Orchestration and routing
- **Focus**: Meeting flow, balanced discussion, decision readiness
- **Output**: Routing decisions, meeting progression

## API Reference

### `run_board_meeting(query, thread_id=None, use_premium=False, stream=False)`

Run a complete AI Board of Directors meeting.

**Parameters:**
- `query` (str): Business question or decision to discuss
- `thread_id` (str, optional): Unique session identifier
- `use_premium` (bool): Use stronger LLM models
- `stream` (bool): Return streaming generator

**Returns:**
```python
{
    "success": bool,
    "thread_id": str,
    "messages": list[BaseMessage],
    "decision": str | None,
    "error": str | None,
    "rounds": int
}
```

### `continue_meeting(thread_id, additional_query)`

Add input to an existing meeting.

### `get_meeting_history(thread_id)`

Retrieve state of an existing meeting.

## Error Handling

The system handles:
- Invalid API keys (ValueError)
- Recursion limits (GraphRecursionError)
- Empty/invalid queries (ValueError)
- Provider failures (Exception with logging)

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Code Style

The project follows:
- PEP 8 guidelines
- Comprehensive type hints
- Google-style docstrings
- Clear separation of concerns

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Follow the existing code style
2. Add type hints to all functions
3. Include docstrings for public APIs
4. Add tests for new features
5. Update documentation as needed

---

Built with LangGraph, LangChain, and modern Python best practices.