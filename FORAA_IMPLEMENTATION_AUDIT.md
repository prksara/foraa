# FORAA IMPLEMENTATION AUDIT

## 1. Existing Architecture
- **Frontend**: React + Vite, Context API for state (`ChatContext`, `AuthContext`), CSS Variables (`App.css`).
- **Backend**: FastAPI, SQLAlchemy (Async), PostgreSQL (Supabase), pgvector.
- **AI**: Groq API (`llama-3.1-70b-versatile` / `llama3-8b-8192`), streaming SSE.
- **Auth**: Supabase Auth (JWT verified in FastAPI `security.py`).

## 2. Existing Components & Pages
- **Pages**: `Home.jsx`, `Assistant.jsx`, `MyHealth.jsx`, `Reports.jsx`, `Nutrition.jsx`, `Wellness.jsx`, `Settings.jsx`, `Login.jsx`.
- **Components**: `AskForraa.jsx` (Home entry point), `Layout.jsx` (Sidebar), `SettingsSection.jsx`, `SettingsRow.jsx`.
- **Status**: The core pages exist. Navigation works. The Assistant UI is highly polished. Settings are now fully persistent via the backend.

## 3. Existing Database Tables (SQLAlchemy Models)
- `users`, `conversations`, `messages`, `health_profiles`, `health_conditions`, `allergies`, `medications`, `lifestyle_entries`, `health_goals`, `measurements`, `health_documents`, `document_extractions`, `health_events`, `user_preferences`.
- **Phase 6 Tables**: `medical_sources`, `knowledge_documents`, `knowledge_chunks`.

## 4. Existing Systems
- **AI Pipeline**: `main.py` -> `intent.py` -> `health_context.py` -> `EvidenceRetrievalService` -> LLM Stream.
- **Memory System**: `memory_extraction.py` uses LLM to identify permanent health facts in the background and writes to `health_events`.
- **Auth**: Working end-to-end via Supabase.
- **Reports**: Simple upload/status tracking.

## 5. Broken / Incomplete Functionality
- **Home -> Assistant Context Transfer**: `AskForraa.jsx` sets `pendingAssistantMessage`. `Assistant.jsx` fires `handleSend` immediately, but if `loading` is still evaluating or if the component hasn't fully hydrated, it might drop or duplicate. Need to verify its persistence.
- **My Health**: Still contains some mocked cards (`Nutrition.jsx` and `Wellness.jsx` are somewhat placeholders, though `MyHealth.jsx` connects to `Measurements` API).
- **RAG Pipeline (Phase 6)**: The ingestion pipeline (`document_processing.py`), chunking logic, embeddings (`embeddings.py`), vector storage population, and reranking are largely stubs or incomplete. `EvidenceRetrievalService` exists but only does basic `pgvector` search against an empty or unpopulated table.
- **Testing**: No comprehensive automated test suite.

## 6. Exact Missing Tasks (Next Steps)
1. Fix Home -> Assistant transfer if it has race conditions.
2. Complete the RAG Ingestion Pipeline (Parsing, Normalizing).
3. Complete the RAG Chunking (Semantic chunking).
4. Complete the RAG Embeddings (HuggingFace/SentenceTransformers or Groq embeddings).
5. Complete RAG Retrieval + Reranking (Cross-encoder or simple score weighting).
6. Verify Evidence -> Citations in Assistant output.
