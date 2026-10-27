# SENTINEL — Verifikasi Informasi

Information-verification workspace for news, messages, images, and links. Live at **https://sentinel.aiclub.ai.id**.

This repository holds two versions of the same app:

| | Static site (repo root) | Flask server (`server/`) |
|---|---|---|
| Hosting | GitHub Pages, no backend | Any Python host (Render, Vercel, local) |
| Who calls the APIs | The visitor's browser, directly | The Flask server, using keys sent per request |
| Article URLs | Tavily Extract (`POST https://api.tavily.com/extract`) | Server-side fetch + BeautifulSoup, with SSRF checks |
| Status | **Production** | Kept for reference |

## Static site (production)

Files: `index.html`, `assets/sentinel.css`, `assets/sentinel.js`, `CNAME`.

The `/api/analyze` logic from `server/app.py` is ported to `assets/sentinel.js`:

1. Validate the input: the 4 MB request budget, PNG/JPG/WEBP images up to 8 MB (larger images are downscaled), and the `data:image/...;base64,` format.
2. For a news link or social link, get the page text through **Tavily Extract**. If no Tavily key is set or extraction fails, the user is asked to paste the article text.
3. Ask the OpenRouter model to extract up to 3 searchable claims.
4. Search **Tavily** (web) and the **Google Fact Check Tools API** (claim reviews) for each claim, depending on the evidence strategy. Results are de-duplicated by URL.
5. Send the content (and the image, for vision models) plus the evidence to **OpenRouter** chat completions (default model `openai/gpt-4.1-mini`) and render the JSON verdict.

### Bring your own key (BYOK)

- Visitors enter their own OpenRouter key (required) and, optionally, Tavily and Google Fact Check keys in **Pengaturan AI**.
- Keys are kept in `sessionStorage` (or in memory if storage is unavailable). They disappear when the tab closes, and the "Hapus key dari browser" button clears them.
- Each key is sent only to its own provider: `openrouter.ai`, `api.tavily.com`, `factchecktools.googleapis.com`. A Content-Security-Policy `connect-src` limits the page to exactly those hosts. There is no SENTINEL server, so no key ever reaches one.
- API usage is billed to the visitor's own accounts.

### Run locally

```
python3 -m http.server 8000     # then open http://localhost:8000
```

## Flask server (reference, `server/`)

The original backend version. Keys are also BYOK, sent per request in `X-OpenRouter-Key`, `X-Tavily-Key`, and `X-FactCheck-Key` headers and never stored.

```
cd server
pip install -r requirements.txt
python app.py                    # http://127.0.0.1:8787
python -m unittest test_app
```

Deploy as a web service with `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120` (health check `/api/health`).

Entry for the .id DeveloperDay competition (PANDI).
