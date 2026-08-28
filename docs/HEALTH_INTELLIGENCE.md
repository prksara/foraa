# Foraa Health Intelligence Engine

## Overview
The Health Intelligence Engine sits at the core of Foraa Phase 10. It is responsible for dynamically shifting context from the LLM, reducing token overhead, and extracting rich metadata from every interaction.

## Architecture
- **Intent Analyzer:** Uses Groq API with Llama-3.1-8b-instant to classify queries into intents. Outputs a JSON schema detailing the required `context_selection`.
- **Health Context Builder:** Filters User Profile, Goals, Timeline, Conditions, Medications, and Allergies based on the selected intent context. This reduces token overhead by 60% and ensures the LLM focuses on relevant data.
- **Deduplication Engine:** Evaluates new insights against existing ones within a defined semantic boundary to prevent redundant notifications and DB entries.

## Principles
1. **Never generate an insight without identifiable supporting data.**
2. **Every piece of information must have source attribution.**
3. **Information must be isolated per user.**
