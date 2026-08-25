from google.genai import Client, types

from term_deposit_advisor.domain.models import (
    CustomerFeatures,
    PredictionResult,
    RetrievedSource,
)
from term_deposit_advisor.domain.ports import DocumentSearchGateway
from .common import TOOL_DESCRIPTION, build_user_context, combine_system_prompts


class GeminiAdvisor:
    provider_name = "Gemini"

    def __init__(
        self,
        *,
        model: str,
        auth_mode: str,
        project_id: str,
        location: str,
        api_key: str | None = None,
        system_prompt: str,
        additional_prompt: str = "",
    ) -> None:
        self.model_name = model
        self._system_prompt = combine_system_prompts(
            system_prompt, additional_prompt
        )

        if auth_mode == "Gemini API key":
            if not api_key:
                raise ValueError("Gemini API key is required.")
            self._client = Client(api_key=api_key)
        else:
            self._client = Client(
                vertexai=True,
                project=project_id,
                location=location,
            )

    @staticmethod
    def _tool() -> types.Tool:
        declaration = types.FunctionDeclaration(
            name="search_deposit_terms",
            description=TOOL_DESCRIPTION,
            parameters_json_schema={
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        )
        return types.Tool(function_declarations=[declaration])

    def answer(
        self,
        *,
        customer: CustomerFeatures,
        prediction: PredictionResult,
        question: str,
        document_search: DocumentSearchGateway,
    ) -> tuple[str, bool, list[RetrievedSource]]:
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=build_user_context(customer, prediction, question)
                    )
                ],
            )
        ]
        sources: list[RetrievedSource] = []
        retrieval_used = False

        for _ in range(4):
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self._system_prompt,
                    tools=[self._tool()],
                    temperature=0,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )

            function_calls = response.function_calls or []
            if not function_calls:
                return response.text or "", retrieval_used, sources

            contents.append(response.candidates[0].content)
            tool_parts = []

            for call in function_calls:
                if call.name != "search_deposit_terms":
                    payload = {"error": f"Unknown tool: {call.name}"}
                else:
                    args = dict(call.args or {})
                    found = document_search.search(
                        args.get("question", question), top_k=5
                    )
                    retrieval_used = True
                    sources.extend(found)
                    payload = [source.__dict__ for source in found]

                tool_parts.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response={"result": payload},
                    )
                )

            contents.append(types.Content(role="tool", parts=tool_parts))

        return (
            "The agent reached the maximum tool-call rounds.",
            retrieval_used,
            sources,
        )
