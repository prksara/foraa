# Architecture Overview

## Tech Stack
- **Frontend:** React + Vite
- **Backend:** FastAPI, PostgreSQL (asyncpg), Supabase Authentication
- **AI Models:** Groq (Llama-3.1-8b-instant) for inference and intent routing
- **Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Database Schema Management:** Direct async execution (`run_init_db.py`) during iterative implementation.

## Phase 10 Architecture Updates
1. **Dynamic Context Building:** `IntentAnalyzer` provides structured output defining what tables to query, ensuring the prompt context window is fully optimized.
2. **Background Agents:** `InsightsEngine` runs as a fire-and-forget task attached to specific create/update health endpoints to deduce intelligence over time.
3. **Schema Entities:** Added `HealthInsight`, `Notification`, and `MemoryItem` with rigorous foreign key mapping to the Supabase `users` table for full multi-tenant isolation.
