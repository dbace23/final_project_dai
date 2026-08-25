import json

from openai import OpenAI

from term_deposit_advisor.domain.models import (
    CustomerFeatures,
    PredictionResult,
    RetrievedSource,
)
from term_deposit_advisor.domain.ports import DocumentSearchGateway
from .common import TOOL_DESCRIPTION, build_user_context, combine_system_prompts


class OpenRouterAdvisor:
    provider_name = "OpenRouter"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        system_prompt: str,
        additional_prompt: str = "",
    ) -> None:
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        self.model_name = model
        self._system_prompt = combine_system_prompts(
            system_prompt, additional_prompt
        )
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    @staticmethod
    def _tools() -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_deposit_terms",
                    "description": TOOL_DESCRIPTION,
                    "parameters": {
                        "type": "object",
                        "properties": {"question": {"type": "string"}},
                        "required": ["question"],
                    },
                },
            }
        ]

    def answer(
        self,
        *,
        customer: CustomerFeatures,
        prediction: PredictionResult,
        question: str,
        document_search: DocumentSearchGateway,
    ) -> tuple[str, bool, list[RetrievedSource]]:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": build_user_context(customer, prediction, question),
            },
        ]
        sources: list[RetrievedSource] = []
        retrieval_used = False

        for _ in range(4):
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self._tools(),
                tool_choice="auto",
                temperature=0,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                return message.content or "", retrieval_used, sources

            messages.append(message.model_dump(exclude_none=True))

            for call in message.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                if call.function.name != "search_deposit_terms":
                    result = {"error": f"Unknown tool: {call.function.name}"}
                else:
                    found = document_search.search(
                        args.get("question", question), top_k=5
                    )
                    retrieval_used = True
                    sources.extend(found)
                    result = [source.__dict__ for source in found]

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.function.name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        return (
            "The agent reached the maximum tool-call rounds.",
            retrieval_used,
            sources,
        )
