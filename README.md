# Marginalia — RAG Chatbot for VERITAS Papers

A demo/portfolio site wrapping your existing LangChain RAG pipeline: FastAPI backend, plain HTML/CSS/JS frontend, warm beige/dark theme, source citations under every answer.

## 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then fill in GOOGLE_API_KEY (and HF_TOKEN if needed)
```

Put your PDFs in `backend/eg_dir/` (matches `PDF_DIR` in `rag_pipeline.py`) — first run will chunk, embed, and persist them to `backend/sample_articles/`. Subsequent runs reuse that store instead of re-embedding.

Run the API:

```bash
uvicorn main:app --reload --port 8000
```

Check it's alive: `http://localhost:8000/health` → `{"status": "ok"}`

## 2. Frontend

No build step — it's static HTML/CSS/JS.

```bash
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500`. If your backend runs anywhere other than `http://localhost:8000`, update `API_BASE_URL` at the top of `frontend/js/app.js`.

## 3. Notes

- **Local model toggle**: the UI already has a Cloud/Local pill switch. Cloud calls your existing Gemini chain. Local currently returns a 501 from the backend as a placeholder — wire up an Ollama-backed chain in `rag_pipeline.py` and branch on `model_mode` in `main.py`'s `/ask` route when you're ready.
- **CORS**: `main.py` currently allows all origins (`"*"`) for easy local testing. Before sharing a public link, set `allow_origins` to your deployed frontend's exact domain.
- **Corpus**: fixed at the PDFs you index at startup (VERITAS papers, per the brief). No upload UI yet — that's real-product territory, not demo territory.
- **Deploy**: frontend → Vercel/Netlify (drag-and-drop the `frontend/` folder). Backend → Render/Railway, or your existing AWS EC2/Docker setup.

## Structure

```
project/
├── backend/
│   ├── main.py           # FastAPI app: POST /ask, GET /health
│   ├── rag_pipeline.py   # your existing RAG chain, unchanged
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html
    ├── css/style.css
    ├── js/app.js
    └── assets/favicon.svg
```
