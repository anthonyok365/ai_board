# AI Board Frontend

A beautiful, modern Streamlit frontend for the AI-powered Board of Directors application.

## Architecture

- **Frontend**: Streamlit Cloud - https://ai-board.streamlit.app
- **Backend**: Render API - https://ai-board-backend-fp0x.onrender.com

## Quick Start (Local Development)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select repository: `anthonyok365/ai_board`
4. Set **Main file path:** `frontend/app.py`
5. Click **Advanced settings** → **Secrets** and add:
   - `BACKEND_API_URL` = `https://ai-board-backend-fp0x.onrender.com`
   - `BACKEND_MODE` = `api`
   - `XAI_API_KEY` = your xAI key
   - `GROQ_API_KEY` = your Groq key

## Project Structure

```
frontend/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── .streamlit/
│   ├── config.toml             # Streamlit settings
│   └── secrets.toml            # Secrets (not committed)
└── components/
    ├── sidebar.py              # Configuration panel
    ├── chat_display.py         # Debate display
    └── decision_panel.py       # Decision summary
```
