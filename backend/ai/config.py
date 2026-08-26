"""
Foraa AI — Configuration.

Reads AI-related settings from environment variables.
Never hardcodes credentials or exposes them through API endpoints.
"""

import os


def get_model_provider() -> str:
    """Return the configured model provider (default: 'groq')."""
    return os.getenv("MODEL_PROVIDER", "groq").lower()


def get_groq_api_key() -> str | None:
    """Return the Groq API key from the environment, or None if missing."""
    return os.getenv("GROQ_API_KEY")


def get_model_name() -> str:
    """Return the model name to use (default: 'llama-3.3-70b-versatile')."""
    return os.getenv("MODEL_NAME", "qwen/qwen3.6-27b")
