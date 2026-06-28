# AI Customer Support Platform

An AI-powered customer support workspace for asking questions over uploaded documents. The app provides a React chat interface, a FastAPI backend, JWT authentication, conversation history, PDF ingestion, vector retrieval with ChromaDB, and streamed AI responses through Groq.

## Features

- Unified login and signup flow using email, password, and optional full name.
- JWT-protected API routes for users, conversations, messages, documents, and chat.
- Conversation management with create, search, rename, delete, and message history.
- PDF upload and indexing into a local ChromaDB vector store.
- Retrieval-augmented chat scoped by user and conversation.
- Streaming assistant responses over server-sent events.
- Source metadata returned with answers when document chunks are retrieved.
- Responsive React dashboard with sidebar, chat window, markdown rendering, copy actions, and document upload.
- PM2 ecosystem file for running backend and frontend preview on a single server.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Axios, React Router |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic Settings, Uvicorn |
| Auth | JWT, passlib, bcrypt |
| AI | Groq API, `llama-3.3-70b-versatile` |
| Retrieval | ChromaDB persistent local store |
| Documents | pypdf for PDF text extraction |
| Deployment | PM2, Vite preview, optional EC2/ngrok/Nginx |

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── ai/                 # PDF parsing, chunking, retrieval, LLM calls
│   │   ├── api/v1/             # FastAPI route modules
│   │   ├── core/               # settings, security, exception handling
│   │   ├── db/                 # SQLAlchemy engine/session setup
│   │   ├── dependencies/       # auth dependency helpers
│   │   ├── models/             # SQLAlchemy models
│   │   ├── repositories/       # database access layer
│   │   ├── schemas/            # request/response schemas
│   │   └── services/           # business logic
│   ├── alembic/                # database migrations
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios client
│   │   ├── components/         # chat, document, layout components
│   │   ├── pages/              # login and dashboard pages
│   │   ├── routes/             # app routes
│   │   └── services/           # frontend API service wrappers
│   ├── package.json
│   └── vite.config.ts
└── ecosystem.json              # PM2 process definitions
```

## How It Works

1. A user signs up or logs in through `POST /api/v1/auth`.
2. The frontend stores the returned access token in `localStorage`.
3. Authenticated users create conversations and upload PDFs.
4. Uploaded PDFs are saved under `backend/uploads`, parsed with `pypdf`, split into overlapping text chunks, and stored in `backend/chroma_db`.
5. When the user asks a question, the backend retrieves relevant chunks for that user and conversation.
6. The backend sends the question, retrieved context, and recent conversation history to Groq.
7. The assistant response streams back to the UI and is saved in the conversation history.

Current document note: the upload validator allows PDF, DOCX, PNG, and JPEG MIME types, but only PDF files are currently parsed and indexed for retrieval.

## Requirements

- Python 3.14 or newer
- `uv`
- Node.js and npm
- Groq API key
- SQLite for the default local setup, or another SQLAlchemy-compatible database URL

## Backend Setup

```bash
cd backend
uv sync
cp .env.example .env
```

Edit `backend/.env`:

```env
APP_NAME=AI Customer Support Platform
APP_VERSION=1.0.0
DEBUG=True

GROQ_API_KEY=your-groq-api-key
DATABASE_URL=sqlite:///./ai_support.db
SECRET_KEY=change-this-to-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=3000000

BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
BACKEND_CORS_ORIGIN_REGEX=
```

Run migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

For local development, use:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_PREVIEW_ALLOWED_HOSTS=
```

Start the frontend:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

## API Overview

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | API status message |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/auth` | Login existing user or create a new user |
| `GET` | `/api/v1/users/me` | Current authenticated user |
| `POST` | `/api/v1/conversations` | Create a conversation |
| `GET` | `/api/v1/conversations` | List conversations |
| `GET` | `/api/v1/conversations/search?q=...` | Search conversations |
| `GET` | `/api/v1/conversations/{id}/messages` | Get message history |
| `PATCH` | `/api/v1/conversations/{id}` | Rename a conversation |
| `DELETE` | `/api/v1/conversations/{id}` | Delete a conversation |
| `POST` | `/api/v1/documents/upload` | Upload a document to a conversation |
| `GET` | `/api/v1/documents?conversation_id=...` | List conversation documents |
| `GET` | `/api/v1/documents/{id}?conversation_id=...` | Get one document |
| `DELETE` | `/api/v1/documents/{id}?conversation_id=...` | Delete a document |
| `POST` | `/api/v1/chat/ask` | Non-streaming answer |
| `POST` | `/api/v1/chat/stream` | Streaming answer via server-sent events |

All `/api/v1/*` routes except authentication require:

```http
Authorization: Bearer <access_token>
```

## Production Build

The frontend API base URL is baked into the Vite build. Set `frontend/.env` before running `npm run build`.

For direct EC2 port testing:

```env
VITE_API_BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000
VITE_PREVIEW_ALLOWED_HOSTS=your-ngrok-host.ngrok-free.dev
```

Then:

```bash
cd frontend
npm run build
```

For same-origin deployment behind Nginx, where frontend and API are served from the same host and Nginx proxies `/api` to FastAPI, use an empty API base:

```env
VITE_API_BASE_URL=
VITE_PREVIEW_ALLOWED_HOSTS=
```

## PM2 Deployment

The repository includes `ecosystem.json` with two processes:

- `ai-support-backend`: runs FastAPI through `uvicorn` on port `8000`.
- `ai-support-frontend`: runs `vite preview` on port `5173` and serves `frontend/dist`.

Start both:

```bash
pm2 start ecosystem.json --update-env
```

Check status:

```bash
pm2 list
pm2 logs ai-support-backend
pm2 logs ai-support-frontend
```

The current frontend preview command binds to `0.0.0.0`, so it can be tested directly at:

```text
http://YOUR_EC2_PUBLIC_IP:5173
```

The backend binds to `0.0.0.0:8000`, so the API can be tested directly at:

```text
http://YOUR_EC2_PUBLIC_IP:8000/health
```

Make sure the EC2 security group allows inbound traffic for the ports you are testing.

## EC2 Direct-Port Environment

Use this when testing without Nginx.

`frontend/.env`:

```env
VITE_API_BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000
VITE_PREVIEW_ALLOWED_HOSTS=your-ngrok-host.ngrok-free.dev
```

`backend/.env`:

```env
APP_NAME=AI Customer Support Platform
APP_VERSION=1.0.0
DEBUG=False

GROQ_API_KEY=your-groq-api-key
DATABASE_URL=sqlite:///./ai_support.db
SECRET_KEY=change-this-to-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=3000000

BACKEND_CORS_ORIGINS=http://YOUR_EC2_PUBLIC_IP:5173
BACKEND_CORS_ORIGIN_REGEX=
```

After changing frontend env values, rebuild the frontend:

```bash
cd frontend
npm run build
pm2 restart ai-support-frontend --update-env
```

After changing backend env values, restart the backend:

```bash
pm2 restart ai-support-backend --update-env
```

## Ngrok Notes

Vite preview validates the request host. If ngrok shows an error such as:

```text
This host is not allowed
```

add the ngrok hostname to `VITE_PREVIEW_ALLOWED_HOSTS`:

```env
VITE_PREVIEW_ALLOWED_HOSTS=your-ngrok-host.ngrok-free.dev
```

If the frontend is opened through an HTTPS ngrok URL and the backend is called over plain HTTP, the browser may block the request as mixed content. For full ngrok testing, expose both frontend and backend through ngrok and build the frontend with the backend ngrok HTTPS URL:

```env
VITE_API_BASE_URL=https://your-backend-ngrok-host.ngrok-free.dev
VITE_PREVIEW_ALLOWED_HOSTS=your-frontend-ngrok-host.ngrok-free.dev
```

Then allow the frontend ngrok origin on the backend:

```env
BACKEND_CORS_ORIGINS=https://your-frontend-ngrok-host.ngrok-free.dev
```

## Troubleshooting

### Frontend calls port 5173 for API and gets 404

The frontend was built with an empty or wrong `VITE_API_BASE_URL` while using direct ports. Set:

```env
VITE_API_BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000
```

Then rebuild `frontend/dist` and restart the frontend process.

### CORS error during login or signup

Make sure the exact frontend origin is present in `BACKEND_CORS_ORIGINS`. Include the scheme and port:

```env
BACKEND_CORS_ORIGINS=http://YOUR_EC2_PUBLIC_IP:5173
```

Restart the backend after changing this value.

### Vite preview blocks ngrok host

Set:

```env
VITE_PREVIEW_ALLOWED_HOSTS=your-ngrok-host.ngrok-free.dev
```

Restart the frontend preview process.

### API works locally but not after deployment

Check all of the following:

- EC2 security group allows the tested ports.
- Backend is listening on `0.0.0.0:8000`.
- Frontend was rebuilt after changing `VITE_API_BASE_URL`.
- Browser network tab shows API calls going to the backend host and port, not the frontend port.
- Backend `.env` contains the frontend origin in `BACKEND_CORS_ORIGINS`.

## Notes

- `backend/uploads`, `backend/chroma_db`, local database files, and environment files are intentionally ignored by Git.
- `frontend/dist` is committed in this project for simple server deployment.
- For production beyond a demo, prefer HTTPS, a real domain, a stricter CORS allow-list, and a durable database/storage setup.
