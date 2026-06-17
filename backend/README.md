# AI Board Backend

LangGraph-powered multi-agent system for AI-powered board meetings.

## Deploy to Render

### Option 1: Blueprint (Recommended)

The `render.yaml` at the repo root configures automatic deployment.

1. Go to [render.com](https://render.com)
2. Click **New** → **Blueprint**
3. Connect your GitHub repo: `anthonyok365/ai_board`
4. Render will find `render.yaml` automatically
5. Add Environment Variables:
   - `LLM_PROVIDER` = `groq` (or `xai`)
   - `GROQ_API_KEY` = your Groq API key
   - `XAI_API_KEY` = your xAI API key
6. Click **Apply**

### Option 2: Manual Web Service

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect GitHub repo: `anthonyok365/ai_board`
3. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r api_requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `LLM_PROVIDER` = `groq`
   - `GROQ_API_KEY` = your key
   - `XAI_API_KEY` = your key

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/meeting` | Start a board meeting |
| POST | `/meeting/continue` | Continue a meeting |
| GET | `/meeting/{thread_id}` | Get meeting history |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `xai` or `groq` | `groq` |
| `XAI_API_KEY` | xAI API key | - |
| `GROQ_API_KEY` | Groq API key | - |
