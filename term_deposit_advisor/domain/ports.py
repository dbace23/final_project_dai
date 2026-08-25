from typing import Protocol

from .models import (
    CustomerFeatures,
    PredictionResult,
    RetrievedSource,
)


class PredictionGateway(Protocol):
    def predict(self, customer: CustomerFeatures) -> PredictionResult:
        ...


class DocumentSearchGateway(Protocol):
    def search(self, question: str, top_k: int = 5) -> list[RetrievedSource]:
        ...


class AdvisorLLM(Protocol):
    provider_name: str
    model_name: str

    def answer(
        self,
        *,
        customer: CustomerFeatures,
        prediction: PredictionResult,
        question: str,
        document_search: DocumentSearchGateway,
    ) -> tuple[str, bool, list[RetrievedSource]]:
        ...
