# Code Weaver Pro - Local Development

This directory contains the modernized Code Weaver Pro platform with a React frontend and enhanced FastAPI backend.

## Directory Structure

```
apps/
  web/          # Next.js 14 frontend (React + TypeScript + shadcn/ui)
  api/          # FastAPI backend with WebSocket support
```

## Quick Start

### Prerequisites

- Node.js 20+ (for frontend)
- Python 3.11+ (for backend)
- npm or yarn

### 1. Start the Backend API

```bash
cd apps/api

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Or (Unix/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

The API will be available at `http://localhost:8000`
- API docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/api/generate/ws/{project_id}

### 2. Start the Frontend

```bash
cd apps/web

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

### Frontend (apps/web)
- Next.js 14 with App Router
- shadcn/ui components
- Zustand for state management
- React Query for data fetching
- Supabase client (optional for production)
- Dark mode by default

### Backend (apps/api)
- FastAPI with async support
- WebSocket for real-time updates
- Server-Sent Events for streaming
- Mock code generation (for local development)
- 52 AI agent simulation

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| GET | /api/projects | List projects |
| POST | /api/projects | Create project |
| GET | /api/projects/{id} | Get project |
| POST | /api/generate | Generate code (SSE stream) |
| WS | /api/generate/ws/{id} | WebSocket generation |
| GET | /api/generate/agents | List available agents |

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Backend (.env)
```
APP_NAME="Code Weaver Pro API"
DEBUG=true
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
```

## Development Workflow

1. **Create a project** - Use the frontend form to describe your app
2. **Watch agents work** - See real-time progress as mock agents process
3. **View generated files** - Examine the generated code

## Next Steps (Roadmap)

- [ ] Phase 2: OpenHands integration for real code execution
- [ ] Phase 2: Multi-LLM router (Claude, GPT-4, etc.)
- [ ] Phase 2: LlamaIndex for codebase understanding
- [ ] Phase 3: WebContainer for live preview
- [ ] Phase 4: GitHub Actions CI/CD

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, TypeScript |
| UI | shadcn/ui, Tailwind CSS, Radix UI |
| State | Zustand, React Query |
| Backend | FastAPI, Pydantic, WebSockets |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth |
