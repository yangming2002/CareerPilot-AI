import json
from dataclasses import dataclass
from typing import TypeVar

from openai import APIError, APITimeoutError, APIConnectionError, OpenAI

T = TypeVar("T")


@dataclass
class LLMConfig:
    model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.3
    max_retries: int = 2
    timeout: float = 30.0


class LLMClient:
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client = OpenAI(timeout=self.config.timeout)

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
                raise  # Don't retry on network errors, let caller handle
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    continue
        raise last_error  # type: ignore[misc]

    def complete_structured(self, system: str, user: str, output_schema: type[T]) -> T:
        """Use OpenAI structured output (JSON mode). Raises on failure."""

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
                        {"role": "user", "content": user},
                    ],
                    response_format={"type": "json_object"},
                )

                raw = response.choices[0].message.content or "{}"
                data = json.loads(raw)
                return output_schema.model_validate(data)

            except (APITimeoutError, APIConnectionError):
                raise  # Network errors — don't retry, let caller degrade

            except APIError as e:
                if attempt < self.config.max_retries:
                    continue
                raise

            except Exception as e:
                # Schema validation or JSON parse error
                if attempt < self.config.max_retries:
                    continue
                raise


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
