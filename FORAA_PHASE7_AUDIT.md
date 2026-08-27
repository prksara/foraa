# Foraa.ai - Phase 7 Audit (Structured Health Reasoning Engine)

This document maps the Phase 7 Reasoning Engine requirements against the existing codebase.

## System Audit

### 1. Existing Systems vs Reasoning Engine Needs
| Feature | Status | Notes / Location |
|---|---|---|
| **Authentication & Users** | `[x]` | JWT + Supabase + SQLAlchemy dependencies. Working perfectly. |
| **Conversations & DB** | `[x]` | `ConversationManager` handles CRUD correctly. |
| **Health Profile & Context** | `[~]` | `HealthContextBuilder` dumps all active context into an XML format. **Lacks contextual relevance filtering** based on the query. |
| **Memory Extraction** | `[x]` | `MemoryExtractor` runs as a fire-and-forget background task. |
| **Intent Analysis** | `[~]` | `IntentAnalyzer` exists and categorizes (`needs_evidence`, `needs_profile`). Needs to be expanded to handle complex decomposition and structured reasoning routing. |
| **Evidence Retrieval (RAG)** | `[x]` | `EvidenceRetrievalService` handles Hybrid Search. |
| **Evidence Reranking** | `[x]` | `Reranker` class utilizes LLM to score relevance. |
| **Chat Streaming (SSE)** | `[~]` | `main.py` handles SSE correctly, but currently only supports `content` and `evidence_metadata` events. Needs `reasoning_status` event type to bubble up reasoning state without exposing private CoT. |
| **AI Generation** | `[~]` | `AIService` wraps Groq calls, but currently is monolithic. Need specialized models/tasks (e.g., validators, structured JSON output parsers). |

### 2. Missing Reasoning Modules (Phase 7 Specific)
| Module | Status | Requirement |
|---|---|---|
| **Reasoning Architecture** | `[ ]` | A dedicated `backend/reasoning/` module structure to orchestrate this logic instead of stuffing it all into `main.py`. |
| **Reasoning State** | `[ ]` | Structured state machine tracking `ReasoningState` for the lifecycle of a request. |
| **Question Decomposition** | `[ ]` | Splitting complex medical queries into sub-questions. |
| **Context Relevance** | `[ ]` | Filtering the `HealthContextBuilder` to avoid token-bloat and noise. |
| **Evidence Mapping** | `[ ]` | Mapping claims to retrieved evidence explicitly. |
| **Contradiction Detection** | `[ ]` | Detecting discrepancies between user history, claims, and medical facts. |
| **Missing Information** | `[ ]` | Safely identifying when the user hasn't provided enough info. |
| **Uncertainty Engine** | `[ ]` | Enforcing calibrated qualitative uncertainty (LOW, MODERATE, HIGH) rather than hallucinated stats. |
| **Reasoning Policy** | `[ ]` | Determining the output path (e.g. `DIRECT_ANSWER`, `ASK_CLARIFICATION`, `SAFETY_ESCALATION`). |
| **Response Validator** | `[ ]` | Bounded retry loop confirming the LLM's final response adheres to citations and safety boundaries. |
| **Database Persistance** | `[ ]` | `reasoning_runs` SQLAlchemy model and Alembic migration for observability. |

---

## Conclusion
The foundation (RAG, Chat, Streaming, DB, Intent) is incredibly solid. The goal of Phase 7 is to construct a **Reasoning Orchestrator** that sits between `Intent Analysis` and `AI Generation`, turning the current linear pipeline into an intelligent, validation-backed multi-step agent workflow.
