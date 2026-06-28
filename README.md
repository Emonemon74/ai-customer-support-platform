# AI Customer Support Platform

An AI-powered customer support workspace for chatting with uploaded documents. Users can create an account, upload PDFs into conversations, and ask questions that are answered using retrieved document context and conversation history.

## Features

- Unified login/signup flow with JWT authentication
- Conversation history with create, search, rename, and delete actions
- PDF upload and text extraction
- Document chunking and retrieval with ChromaDB
- Groq-powered AI answers using `llama-3.3-70b-versatile`
- Streaming chat responses over server-sent events
- Source metadata for retrieved document chunks
- React dashboard with responsive sidebar, markdown rendering, code highlighting, and copy actions

> Note: the upload validator currently accepts a few file MIME types, but only PDFs are parsed and indexed for AI retrieval.

## Tech Stack

| Area | Tools |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Axios |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic Settings |
| Auth | JWT, passlib, bcrypt |
| AI | Groq API |
| Retrieval | ChromaDB |
| Documents | pypdf |
| Runtime | uv, Uvicorn, PM2 |

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── ai/              # parsing, chunking, retrieval, LLM calls
│   │   ├── api/v1/          # FastAPI routes
│   │   ├── core/            # settings, security, exception handlers
│   │   ├── db/              # database session setup
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # database access
│   │   ├── schemas/         # request/response schemas
│   │   └── services/        # business logic
│   └── alembic/             # migrations
├── frontend/
│   └── src/
│       ├── api/             # Axios client
│       ├── components/      # UI components
│       ├── pages/           # Login and dashboard
│       ├── routes/          # React routes
│       └── services/        # API wrappers
└── ecosystem.json           # PM2 process config
```

## How It Works

1. A user signs up or logs in through the unified auth endpoint.
2. The frontend stores the JWT access token and sends it with API requests.
3. A user creates or selects a conversation.
4. Uploaded PDFs are saved, parsed, chunked, and indexed in ChromaDB.
5. Chat questions retrieve relevant chunks scoped to the current user and conversation.
6. Groq generates an answer using the retrieved context and recent conversation history.
7. The answer streams back to the frontend and is saved in the message history.

## Backend Setup

```bash
cd backend
uv sync
cp .env.example .env
```

Example `backend/.env`:

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

Run migrations and start the API:

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

Example `frontend/.env`:

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

## Main API Routes

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/auth` | Login or signup |
| `GET` | `/api/v1/users/me` | Current user |
| `GET` | `/api/v1/conversations` | List conversations |
| `POST` | `/api/v1/conversations` | Create conversation |
| `GET` | `/api/v1/conversations/{id}/messages` | Conversation messages |
| `POST` | `/api/v1/documents/upload` | Upload document |
| `POST` | `/api/v1/chat/ask` | Non-streaming chat answer |
| `POST` | `/api/v1/chat/stream` | Streaming chat answer |

Protected routes require:

```http
Authorization: Bearer <access_token>
```

## Build and PM2

Build the frontend:

```bash
cd frontend
npm run build
```

Run both services with PM2:

```bash
pm2 start ecosystem.json --update-env
```

The PM2 config starts:

- backend on port `8000`
- frontend preview on port `5173`

## Notes

- Local uploads are stored in `backend/uploads`.
- ChromaDB data is stored in `backend/chroma_db`.
- Local database files, uploaded files, vector data, and env files are ignored by Git.
- `frontend/dist` is included for simple server deployment.
