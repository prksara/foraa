# Foraa Memory Governance

## Overview
Memory Governance ensures that Foraa's AI does not arbitrarily remember or manipulate facts about a user without their explicit consent.

## Data Model
- `MemoryItem`
  - `id`: UUID
  - `user_id`: UUID
  - `content`: str (The explicitly stated fact)
  - `category`: str (e.g., 'diet', 'lifestyle', 'preference')
  - `source`: str (e.g., 'user_explicit', 'extracted_from_report')
  - `source_id`: UUID (Optional reference to report or chat)

## User Control
Users have a dedicated `AI Memory` tab in their Settings dashboard where they can:
1. **View** every single explicitly stored memory that Foraa uses across sessions.
2. **Delete** memories they deem incorrect or no longer relevant.
3. **Opt-out** of specific AI data preference models (e.g., `ai_data_pref`).

## Implementation Details
Memory items are surfaced to the LLM via `HealthContextBuilder` and strictly bound to the user's explicit approval state.
