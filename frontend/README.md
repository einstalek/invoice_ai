# Inflow Frontend

Next.js app for the Inflow invoice processing platform.

## Tech Stack

- **Next.js 16** (App Router, Turbopack)
- **React 19** + **TypeScript**
- **Tailwind CSS 4**
- **@react-oauth/google** for Google OAuth flows
- **@heroicons/react** for icons

## Prerequisites

- **Node.js 20+**
- **npm** (or yarn/pnpm/bun)
- The backend API running (see `backend/README.md`)

## Setup

```bash
# Install dependencies
npm install

# Copy env file and configure
cp .env.example .env.local  # then fill in values (see table below)

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

Create a `.env.local` file in the `frontend/` directory.

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | (empty) | Google OAuth client ID — enables Google login and Google Sheets connect |

> **Important:** `NEXT_PUBLIC_` prefix is required for Next.js to expose these to the browser. Without `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, the Google login button and Google Sheets connect button will not appear.

### Where to get `NEXT_PUBLIC_GOOGLE_CLIENT_ID`

This is the **same** OAuth client ID used by the backend. See the backend README for setup instructions. The value should match `GOOGLE_CLIENT_ID` in the backend's `.env`.

### Example `.env.local` file

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
```

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start development server with Turbopack (port 3000) |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

## Project Structure

```
frontend/src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout (GoogleOAuthProvider, AuthProvider)
│   ├── login/              # Login + registration page
│   └── orgs/[orgId]/       # Organization pages
│       ├── invoices/       # Invoice list + detail
│       └── settings/       # Organization settings (ERP config, Google Sheets)
├── components/             # Shared UI components
│   ├── app-shell.tsx       # Main app layout with sidebar
│   ├── google-login-button.tsx
│   └── google-oauth-wrapper.tsx
└── lib/
    ├── api.ts              # API client (all backend calls)
    ├── auth-context.tsx    # Auth state provider
    └── types.ts            # TypeScript interfaces
```

## Running the Full Stack Locally

You need **three** processes running (four if using PostgreSQL):

| # | Service | Command | Directory | Port |
|---|---|---|---|---|
| 1 | Backend API | `python manage.py runserver` | `backend/` | 8000 |
| 2 | Celery worker | `celery -A config worker -l info` | `backend/` | — |
| 3 | Frontend | `npm run dev` | `frontend/` | 3000 |
| — | Redis | `redis-server` | — | 6379 |

> Redis must be running before starting the Celery worker. See `backend/README.md` for Redis installation.
