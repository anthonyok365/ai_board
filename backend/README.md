# AI Board Backend

LangGraph-powered multi-agent system for AI-powered board meetings.

## Deploy to Render

### Option 1: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Click the button above or go to [render.com](https://render.com)
2. Connect your GitHub account
3. Select this repository: `anthonyok365/ai_board`
4. Set:
   - **Root Directory:** `backend`
   - **Branch:** `main`
5. Add Environment Variables:
   - `LLM_PROVIDER` = `groq` (or `xai`)
   - `GROQ_API_KEY` = your Groq API key
   - `XAI_API_KEY` = your xAI API key
6. Click **Create Web Service**

### Option 2: Manual Deploy via CLI

```bash
# Install Render CLI
brew install render-cli

# Login
render login

# Deploy
cd backend
render deploy --spec render.yaml
```

### Option 3: Clone and Deploy

```bash
# Clone the repo
git clone https://github.com/anthonyok365/ai_board.git
cd ai_board/backend

# Create a new Render Web Service manually
# Settings:
# - Build Command: pip install -r api_requirements.txt
# - Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/meeting` | Start a new board meeting |
| POST | `/meeting/continue` | Continue an existing meeting |
| GET | `/meeting/{thread_id}` | Get meeting history |
| POST | `/config` | Update LLM configuration |

## API Usage

```bash
# Start a meeting
curl -X POST https://your-backend.onrender.com/meeting \
  -H "Content-Type: application/json" \
  -d '{"query": "Should we invest $800k in AI expansion?"}'

# Continue a meeting
curl -X POST https://your-backend.onrender.com/meeting/continue \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "abc123", "query": "What about the risks?"}'
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_PROVIDER` | `xai` or `groq` | Yes |
| `XAI_API_KEY` | xAI API key | If using xAI |
| `GROQ_API_KEY` | Groq API key | If using Groq |

## Models

- **xAI**: `grok-4.3`
- **Groq**: `meta-llama/llama-4-scout-17b-16e-instruct`
