from term_deposit_advisor.domain.models import AdvisorRequest, AdvisorResult
from term_deposit_advisor.domain.ports import (
    AdvisorLLM,
    DocumentSearchGateway,
    PredictionGateway,
)


class AnalyzeCustomerUseCase:
    """Application orchestration only; no framework/vendor code lives here."""

    def __init__(
        self,
        prediction_gateway: PredictionGateway,
        document_search: DocumentSearchGateway,
        llm: AdvisorLLM,
    ) -> None:
        self._prediction_gateway = prediction_gateway
        self._document_search = document_search
        self._llm = llm

    def execute(self, request: AdvisorRequest) -> AdvisorResult:
        prediction = self._prediction_gateway.predict(request.customer)

        answer, retrieval_used, sources = self._llm.answer(
            customer=request.customer,
            prediction=prediction,
            question=request.question,
            document_search=self._document_search,
        )

        return AdvisorResult(
            prediction=prediction,
            answer=answer,
            provider=self._llm.provider_name,
            model=self._llm.model_name,
            retrieval_used=retrieval_used,
            sources=sources,
        )
