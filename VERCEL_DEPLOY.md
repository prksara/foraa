# Vercel deployment setup

This repository contains a Vite React frontend in `frontend/web` and a FastAPI backend in `backend`.

## Frontend deployment

1. In Vercel, create a new project and set the project root to `frontend/web`.
2. Use the build command:
   - `npm install`
   - `npm run build`
3. Set these environment variables in the Vercel project settings:
   - `VITE_API_URL` = your deployed backend URL, for example `https://your-backend-url.vercel.app` or `https://your-render-url.onrender.com`
   - `VITE_SUPABASE_URL` = your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` = your Supabase anon key
4. Deploy.

## Backend

The API in `backend` is a FastAPI service and is not normally deployable as a static Vercel frontend. It should be hosted separately on a service that supports Python/FastAPI, such as Render, Railway, Fly.io, or a custom server.

The frontend will call the backend via `VITE_API_URL`.

## SPA routing

The included `frontend/web/vercel.json` ensures client-side routes fall back to `index.html`, which is required for React Router pages like `/assistant/123` and `/health`.
