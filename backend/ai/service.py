"""
Foraa AI — Service layer.

Provides AIService, which abstracts the LLM provider behind a simple interface.
Currently backed by Groq (Llama). Designed so the provider can be swapped later
without changing the rest of the application.
"""

import logging

from groq import Groq, APIError, AuthenticationError, RateLimitError

from .config import get_groq_api_key, get_model_name, get_model_provider
from .prompts import FORAA_SYSTEM_PROMPT


logger = logging.getLogger("foraa.ai")


class AIServiceError(Exception):
    """Raised when the AI service encounters a recoverable error."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class AIService:
    """
    High-level interface to the AI backend.

    Usage:
        service = AIService()
        reply = service.generate_response("I have a headache.")
    """

    def __init__(self) -> None:
        provider = get_model_provider()
        if provider != "groq":
            raise AIServiceError(
                f"Unsupported model provider: '{provider}'. "
                "Currently only 'groq' is supported.",
                status_code=500,
            )

        api_key = get_groq_api_key()
        if not api_key:
            raise AIServiceError(
                "GROQ_API_KEY is not set. "
                "Please add it to your .env file.",
                status_code=500,
            )

        self._client = Groq(api_key=api_key)
        self._model = get_model_name()
        logger.info("AIService initialized — provider=%s, model=%s", provider, self._model)

    def _sanitize_response(self, text: str) -> str:
        """
        Sanitize the model's raw output by stripping out hidden reasoning tags,
        internal instructions, and orchestration details before it reaches the user.
        """
        import re
        if not text:
            return ""
        
        # Remove <think>...</think> blocks, including across multiple lines
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        
        # Strip trailing/leading whitespace left behind
        return cleaned.strip()

    def generate_response(self, user_message: str) -> str:
        """
        Send a user message to the LLM and return the assistant's reply.

        Raises AIServiceError on any provider/validation failure.
        """
        if not user_message or not user_message.strip():
            raise AIServiceError("Message cannot be empty.", status_code=400)

        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": FORAA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message.strip()},
                ],
                temperature=0.6,
                max_tokens=1024,
            )

            reply = completion.choices[0].message.content
            if not reply:
                raise AIServiceError(
                    "The model returned an empty response. Please try again.",
                    status_code=502,
                )
            
            return self._sanitize_response(reply)

        except AuthenticationError:
            logger.error("Groq authentication failed — check GROQ_API_KEY")
            raise AIServiceError(
                "AI service authentication failed. Please check the API key.",
                status_code=401,
            )
        except RateLimitError:
            logger.warning("Groq rate limit reached")
            raise AIServiceError(
                "AI service is temporarily busy. Please try again in a moment.",
                status_code=429,
            )
        except APIError as exc:
            logger.error("Groq API error: %s", exc)
            raise AIServiceError(
                "AI service encountered an error. Please try again.",
                status_code=502,
            )
        except Exception as exc:
            logger.error("Unexpected AI error: %s", exc)
            raise AIServiceError(
                "An unexpected error occurred. Please try again.",
                status_code=500,
            )

    def generate_stream(self, messages: list[dict]):
        """
        Send a conversation to the LLM and stream the assistant's reply.
        Yields sanitized chunks of text.
        """
        if not messages:
            raise AIServiceError("Messages cannot be empty.", status_code=400)

        # Ensure the system prompt is at the start
        if messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": FORAA_SYSTEM_PROMPT})
        
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.6,
                max_tokens=1024,
                stream=True,
            )

            in_think_block = False
            buffer = ""

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    buffer += content
                    
                    # Process buffer for <think> tags
                    while True:
                        if not in_think_block:
                            think_start = buffer.find("<think>")
                            if think_start != -1:
                                # Yield everything before <think>
                                if think_start > 0:
                                    yield buffer[:think_start]
                                buffer = buffer[think_start + 7:]
                                in_think_block = True
                            else:
                                # We might be in the middle of receiving "<think>".
                                # If buffer ends with something that could be a partial tag, we wait.
                                # A simple approach: yield everything except the last 7 chars if they contain '<'
                                yield_idx = len(buffer)
                                last_lt = buffer.rfind("<")
                                if last_lt != -1 and len(buffer) - last_lt < 7:
                                    yield_idx = last_lt
                                
                                if yield_idx > 0:
                                    yield buffer[:yield_idx]
                                    buffer = buffer[yield_idx:]
                                break
                        else:
                            # We are inside a think block
                            think_end = buffer.find("</think>")
                            if think_end != -1:
                                # Skip past </think>
                                buffer = buffer[think_end + 8:]
                                in_think_block = False
                            else:
                                # Still inside think block, wait for closing tag.
                                break

            # Yield remaining buffer if any (and we're not inside a think block)
            if buffer and not in_think_block:
                yield buffer

        except AuthenticationError:
            logger.error("Groq authentication failed — check GROQ_API_KEY")
            raise AIServiceError(
                "AI service authentication failed. Please check the API key.",
                status_code=401,
            )
        except RateLimitError:
            logger.warning("Groq rate limit reached")
            raise AIServiceError(
                "AI service is temporarily busy. Please try again in a moment.",
                status_code=429,
            )
        except APIError as exc:
            logger.error("Groq API error: %s", exc)
            raise AIServiceError(
                "AI service encountered an error. Please try again.",
                status_code=502,
            )
        except Exception as exc:
            logger.error("Unexpected AI error: %s", exc)
            raise AIServiceError(
                "An unexpected error occurred. Please try again.",
                status_code=500,
            )
