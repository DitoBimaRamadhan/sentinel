# SENTINEL

Information-verification workspace (news, messages, images, links) built with Flask.
Bring-your-own-key: each user enters their own OpenRouter / Tavily / Google Fact Check API keys in the settings panel; keys are sent per request in headers and are not stored on the server.

## Run locally
```
pip install -r requirements.txt
python app.py            # http://127.0.0.1:8787
python -m unittest test_app
```

## Deploy (Render web service)
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
- Health check: `/api/health`

Entry for the .id DeveloperDay competition (PANDI).
