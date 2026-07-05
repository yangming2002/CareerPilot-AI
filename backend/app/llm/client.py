import json
from dataclasses import dataclass
from typing import TypeVar

from openai import APIError, APITimeoutError, APIConnectionError, OpenAI

from app.core.config import (
    LLM_MAX_RETRIES,
    LLM_TIMEOUT,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)

T = TypeVar("T")


@dataclass
class LLMConfig:
    model: str = OPENAI_MODEL
    max_tokens: int = 8192
    temperature: float = 0.3
    max_retries: int = LLM_MAX_RETRIES
    timeout: float = LLM_TIMEOUT


class LLMClient:
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        import httpx
        http_client = httpx.Client(
            timeout=self.config.timeout,
            http2=False,
        )
        self._client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            http_client=http_client,
        )

    @property
    def client(self) -> OpenAI:
        return self._client

    def complete(self, system: str, user: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                return response.choices[0].message.content or ""
            except (APITimeoutError, APIConnectionError) as e:
                raise
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    continue
        raise last_error  # type: ignore[misc]

    def complete_structured(self, system: str, user: str, output_schema: type[T]) -> T:
        schema_json = output_schema.model_json_schema()
        schema_str = json.dumps(schema_json, ensure_ascii=False, indent=2)

        structured_system = (
            system
            + f"\n\nYou MUST respond with a single JSON object matching this schema:\n```json\n{schema_str}\n```\n"
            + "Reply ONLY with the JSON object, no markdown fences, no extra text."
        )

        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[
                        {"role": "system", "content": structured_system},
                        {"role": "user", "content": user + "\n(Please respond with a JSON object.)"},
                    ],
                    response_format={"type": "json_object"},
                )

                raw = response.choices[0].message.content or "{}"
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    # Try to salvage truncated JSON
                    raw = _repair_truncated_json(raw)
                    data = json.loads(raw)
                return output_schema.model_validate(data)

            except (APITimeoutError, APIConnectionError):
                raise

            except APIError as e:
                if attempt < self.config.max_retries:
                    continue
                raise

            except Exception as e:
                if attempt < self.config.max_retries:
                    continue
                raise


def _repair_truncated_json(raw: str) -> str:
    """Try to salvage truncated JSON by closing unclosed strings and brackets."""
    # Balance braces and brackets
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in raw:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in '{[':
            stack.append(ch)
        elif ch in '}]':
            if stack and ((ch == '}' and stack[-1] == '{') or (ch == ']' and stack[-1] == '[')):
                stack.pop()

    # Close unclosed string if needed
    if in_string:
        raw = raw + '"'

    # Close remaining brackets
    for opener in reversed(stack):
        raw = raw + ('}' if opener == '{' else ']')

    return raw


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

