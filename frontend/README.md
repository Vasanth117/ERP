# College ERP — Frontend

Next.js (App Router) + TypeScript + React UI for the FastAPI backend.

## Stack

- **Next.js** — routing, proxy (auth gate), auth BFF routes
- **Tailwind CSS + shadcn/ui** — components
- **TanStack Query** — server state
- **react-hook-form + Zod** — forms
- **TanStack Table** — data grids (ready for module screens)

## Prerequisites

- Node.js 20+
- Docker (MongoDB, Redis, RabbitMQ) and **FastAPI on port 8000** — the login BFF proxies to the backend; if uvicorn is not running you get `ECONNREFUSED` / login 500.

## Setup

**1. Infra** (repo root):

```bash
docker compose up -d mongodb redis rabbitmq
```

**2. Backend** (separate terminal, keep it running):

```bash
cd backend
..\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```

Confirm [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) loads before signing in.

**3. Frontend**:

```bash
cd frontend
cp .env.example .env.local   # optional; defaults match backend CORS
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — **Main Landing Page** (Figma `Main Landing Page` / frame **Select an Entry Point**, node `338:279`).

Module cards route to `/under-construction?module=…` (Figma **Page Under Construction**, node `342:214`) until real workspaces exist.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI origin |
| `NEXT_PUBLIC_API_PREFIX` | `/api/v1` | API version prefix |

## Auth flow

1. Browser posts credentials to `POST /api/auth/login` (Next BFF).
2. BFF calls `POST /api/v1/auth/login`, stores **refresh token** in an httpOnly cookie, returns **access token** to the client.
3. Client keeps the access token in session storage for `Authorization: Bearer` on API calls.
4. `src/proxy.ts` uses the `erp_session` cookie to guard portal routes.

## Project layout

```
src/
  app/
    (auth)/login          # public auth
    (portal)/dashboard    # authenticated shell
    api/auth/*            # login / refresh / logout BFF
  components/             # shared UI
  features/               # domain hooks + API (start with auth)
  lib/api/                # envelope + fetch client
  lib/auth/               # tokens + cookies
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript check |

## Next steps

- Add OpenAPI codegen (`npm run generate:api` placeholder in package.json)
- Role-based route groups: `student`, `faculty`, `platform`, `college-admin`
- Figma page mapping via `design/figma-pages.json`