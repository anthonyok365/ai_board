# AI Board Backend

LangGraph-powered multi-agent system for AI-powered board meetings with Supabase persistence.

## Deploy to Render

1. Go to [render.com](https://render.com) → **New** → **Blueprint**
2. Connect GitHub repo: `anthonyok365/ai_board`
3. Render will find `render.yaml` automatically
4. Add Environment Variables:
   - `LLM_PROVIDER` = `groq`
   - `GROQ_API_KEY` = your Groq API key
   - `XAI_API_KEY` = your xAI API key
   - `SUPABASE_URL` = your Supabase project URL
   - `SUPABASE_KEY` = your Supabase anon key

## Set Up Supabase

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to **SQL Editor** and run this schema:

```sql
CREATE TABLE IF NOT EXISTS meetings (
    id BIGSERIAL PRIMARY KEY,
    thread_id VARCHAR(255) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    result JSONB,
    messages JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all" ON meetings FOR ALL USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_meetings_thread_id ON meetings(thread_id);
CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at DESC);
```

4. Get your credentials from **Settings** → **API**:
   - **Project URL**: Use as `SUPABASE_URL`
   - **anon public**: Use as `SUPABASE_KEY`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/meeting` | Start a board meeting |
| POST | `/meeting/continue` | Continue a meeting |
| GET | `/meeting/{thread_id}` | Get meeting by ID |
| GET | `/meetings` | List all meetings |
| GET | `/schema` | Get SQL schema |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `xai` or `groq` |
| `XAI_API_KEY` | xAI API key |
| `GROQ_API_KEY` | Groq API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
