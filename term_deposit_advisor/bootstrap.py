from google.cloud import bigquery

from term_deposit_advisor.application.advisor_service import AnalyzeCustomerUseCase
from term_deposit_advisor.config import AppConfig
from term_deposit_advisor.infrastructure.bigquery_prediction import (
    BigQueryPredictionGateway,
)
from term_deposit_advisor.infrastructure.bigquery_rag import (
    BigQueryDocumentSearchGateway,
)
from term_deposit_advisor.infrastructure.bigquery_runtime_config import (
    BigQueryRuntimeConfigRepository,
)


def build_use_case(
    *,
    config: AppConfig,
    bq_client: bigquery.Client,
    provider: str,
    gemini_auth_mode: str = "Vertex AI / ADC",
    gemini_api_key: str | None = None,
    openrouter_api_key: str | None = None,
) -> AnalyzeCustomerUseCase:
    runtime_repository = BigQueryRuntimeConfigRepository(bq_client, config)
    runtime = runtime_repository.banking()
    predictor = BigQueryPredictionGateway(bq_client, config, runtime_repository)
    document_search = BigQueryDocumentSearchGateway(bq_client, config)

    if provider == "Gemini":
        try:
            from term_deposit_advisor.infrastructure.llm.gemini import GeminiAdvisor
        except (ImportError, ModuleNotFoundError) as exc:
            raise RuntimeError(
                "Gemini provider requires the google-genai package. "
                "Run: python -m pip install -U google-genai"
            ) from exc
        llm = GeminiAdvisor(
            model=config.gemini_model,
            auth_mode=gemini_auth_mode,
            project_id=config.project_id,
            location=config.vertex_location,
            api_key=gemini_api_key,
            system_prompt=runtime.system_prompt,
            additional_prompt=runtime.additional_prompt,
        )
    elif provider == "OpenRouter":
        from term_deposit_advisor.infrastructure.llm.openrouter import OpenRouterAdvisor
        llm = OpenRouterAdvisor(
            api_key=openrouter_api_key or "",
            model=config.openrouter_model,
            base_url=config.openrouter_base_url,
            system_prompt=runtime.system_prompt,
            additional_prompt=runtime.additional_prompt,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return AnalyzeCustomerUseCase(
        prediction_gateway=predictor,
        document_search=document_search,
        llm=llm,
    )
