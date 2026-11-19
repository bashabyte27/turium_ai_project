# AI Knowledge Inbox

A small web app where you can save notes and web page links, and later ask questions about
what you saved. The answer comes with numbered sources, so you can see exactly which note or
page it was taken from.

I made this for the Full Stack Developer assignment of Turium AI. In this README I have
explained how to run it, how it is built, why I made certain choices, and what is still missing.

## What it does

- Save a text note, or save a URL (the server downloads the page and reads its text).
- Each item shows a status: Processing, Ready or Failed (with the reason).
- Ask a question in your own words. Search is by meaning, not by exact words. So if you saved
  "we deploy every Friday" and ask "when do we release?", it still finds the note.
- The answer comes with numbered sources and the matching text.

## Quick start

You need **Python 3.11+** and **Node.js 20.19+**. No API key is needed to run it.
The first run needs internet, to install packages and to download the embedding model (about 65 MB).

**Backend** (first terminal):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # on Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Start the server from inside the `backend` folder. API docs are at http://localhost:8000/docs.

**Frontend** (second terminal):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The backend must be running at the same time.

I tested all this on Windows 11. I have not run the Mac/Linux commands, but they are the same
except for the activate line.

### Try it

1. Save a note: `Our team deploys to production every Friday afternoon.`
2. Save a URL: `https://www.python.org/about/`
3. Wait till both show "Ready". The first one takes a few seconds because the model is loading.
4. Ask: `When do we release?` You will get the answer with `[1]` style numbers and the source cards.
5. To see error handling, save `http://127.0.0.1:8000/health`. It will fail with a message that
   private addresses are not allowed.

### Run the tests

```bash
cd backend
python -m pytest
```

There are 23 tests. 22 run in under a second and 1 is skipped, because it calls the real Gemini
API and needs `GEMINI_LIVE_KEY`. The tests use a temporary database and a small offline embedder,
so they need no internet and no key.

### Optional: real LLM answers

Without a key, the app answers by quoting the best matching sentences from your saved text.
If you want answers written by an LLM:

1. Copy `backend/.env.example` to `backend/.env`.
2. Put your key in it. `GEMINI_API_KEY` is the easiest one. For OpenAI, Ollama or Groq, use
   `LLM_API_KEY`, `LLM_BASE_URL` and `LLM_MODEL` instead.
3. Restart the backend.

The `.env` file is read automatically (when the server is started from the `backend` folder) and
it is ignored by Git. Other settings like chunk size or `TOP_K` are listed in
`backend/app/config.py`, and each one can be changed with an environment variable.

## Technology used

| Part | Choice | Why |
|---|---|---|
| Backend | Python, FastAPI | Allowed by the assignment. Gives request validation and a free `/docs` page. Background tasks are also built in. |
| Database | SQLite | One file, nothing to install. |
| Embeddings | `fastembed` with `BAAI/bge-small-en-v1.5` | Runs on the local machine, so the app works without any API key. |
| Vector search | NumPy | The search is one matrix multiplication. |
| Page download | `httpx` and `trafilatura` | `trafilatura` removes menus and scripts, so only the readable text is stored. |
| Frontend | React 19 with hooks, Vite, Tailwind CSS 4 | Simple and fast. All API calls are in one file, `src/api.js`. |

## How it is organised

```
backend/app/
  main.py          app setup, request logging, routers
  config.py        all settings with defaults
  database.py      SQLite connection and tables
  schemas.py       request and response shapes
  errors.py        common error format
  logger.py        JSON log lines
  embedder.py      the only file that uses the embedding model
  llm.py           the only file that calls the LLM API
  routers/         ingest.py, items.py, query.py (HTTP only, no logic)
  services/        ingestion, fetcher, chunking, search, answering (the real work)
  repositories/    items.py, chunks.py (the only place where SQL is written)
frontend/src/
  App.jsx, api.js
  hooks/           useItems.js, useAsk.js
  components/      AddItemForm.jsx, ItemList.jsx, AskBox.jsx
```

Routers only take the request and return the response. Services do the work. Repositories talk to
the database. Because of this, any one layer can be changed without touching the others.

## API

| Endpoint | What it does | Success code |
|---|---|---|
| `POST /ingest` | Save a note (`{"type":"note","content":"..."}`) or a URL (`{"type":"url","url":"..."}`) | 202 |
| `GET /items` | List all saved items, newest first, with status | 200 |
| `POST /query` | Ask a question (`{"question":"..."}`), get answer and sources | 200 |
| `GET /health` | Check that the server is up | 200 |

Every error has the same shape:

```json
{ "error": { "code": "validation_error", "message": "Invalid request.", "details": [ ... ] } }
```

Status codes: `422` for bad input (empty note, bad URL, question shorter than 3 characters),
`502` when the LLM service fails, `500` for a real bug (the user sees only "Something went wrong",
and the real error goes to the log).

A sample answer from `POST /query`:

```json
{
  "answer": "Our team deploys to production every Friday afternoon. [1]",
  "mode": "extractive",
  "sources": [
    { "number": 1, "title": "Our team deploys to production every Friday afternoon. Rollb",
      "source_url": null, "snippet": "Our team deploys ...", "score": 0.5586 }
  ]
}
```

`mode` is `llm`, `extractive` (quoted from saved text) or `none` (nothing saved yet).

## How it works

**Saving.** `POST /ingest` saves the item with status `pending` and replies at once. The slow
work (downloading, chunking, embedding) runs in a FastAPI background task. The frontend checks
`GET /items` every 2 seconds while anything is pending. I did it this way because downloading a
page and loading the model can take several seconds, and the user should not wait on a frozen
screen. If the background work fails, the item is marked `failed` with the reason. It is shown in
the list and is not an error popup.

**Chunking.** Text is split at paragraphs first, then at sentences, and only at a word boundary
if a sentence is too long. Chunks are about 800 characters, with 100 characters of overlap. Small
chunks make the search more exact, splitting at sentences avoids cutting an idea in half, and the
overlap helps when an idea sits on the border of two chunks.

**Embeddings and storage.** Each chunk becomes 384 numbers and is stored as raw bytes in the
`chunks` table of the same SQLite file. There is no separate vector database. Every chunk also
stores the model name, because vectors from different models cannot be compared.

**Searching.** The question is embedded and compared with every saved chunk (one dot product),
and the top 5 are returned.

**Answering.**
- *LLM mode* (when a key is set): the numbered chunks and the question go to the LLM, and it is
  told to use only these sources and to add `[n]` after each claim.
- *Extractive mode* (no key, or the LLM call failed): the best 3 matching sentences are copied
  word for word, each followed by its source number. Nothing is written by a model, so nothing
  can be made up.

**URL safety.** Before downloading, the server resolves the hostname and refuses localhost,
private, link-local and reserved addresses. This stops someone from using the server to reach
internal addresses. Downloads have a 10 second timeout and a 2 MB limit, and only text/HTML is accepted.

**Logging.** One JSON object per line, for example `ingest_failed`, `query_answered`, and a
`request` line with method, path, status, time and a request id.

## Tradeoffs I made

- **SQLite plus NumPy instead of a vector database.** It is exact, simple and easy to explain, and
  it is fine for a personal inbox. But every question reads all vectors, so it will become slow when
  data grows.
- **Local embedding model.** No key or cost, and it works offline. But the first request is slow
  and the model is lower quality than the big hosted ones.
- **Background task inside the web server instead of a job queue.** Much less setup. But the work
  is lost if the server stops in the middle.
- **Extractive fallback.** The app is useful even without an LLM, and it never invents anything.
  But the answers read like quoted lines and not like a written answer.

## Known limitations

- **No relevance cut-off.** The top 5 chunks are always returned, even if none of them is related.
  In my testing, asking about something never saved still gave a sentence from an unrelated page.
- **LLM citations are not checked.** In LLM mode the `[n]` numbers come from the model, and the
  code does not verify them. I tested this path with a fake server in the tests, and with a real
  Gemini call only in a manual run, so I would not call it fully tested.
- **Some URLs do not work.** Sites that block scrapers (Wikipedia gave me 403), pages that need
  JavaScript, and PDFs. Some page boilerplate also gets into the saved text.
- **Redirects are not re-checked.** The private-address check is done only on the URL the user gave.
- **No edit or delete,** and the same note or URL saved twice becomes two items.
- **A stopped server leaves items `pending`,** and there is no retry.
- **Single user, no login, no pagination** on `GET /items`.
- **No frontend tests.** Backend tests do not use the real embedding model or the real network.
- Changing `EMBEDDING_MODEL` makes old chunks ignored in search, so items must be added again.

## What I would do for production

1. Move vectors to Postgres with `pgvector` (or a vector database) with an HNSW index. The change
   would be inside `services/search.py` and `repositories/chunks.py` only.
2. Use a proper job queue (Celery, RQ or Arq) with retries.
3. Add login, per-user data, pagination, delete and re-fetch, and duplicate detection.
4. Add a minimum score so the app can say "I could not find this in your notes", and check that
   the LLM citations really match the sources.
5. Combine keyword and vector search, and add a re-ranker.
6. Check every redirect for private addresses, remove boilerplate better, and support
   JavaScript-heavy pages and PDFs.
7. Add frontend tests, Docker and a CI pipeline.
