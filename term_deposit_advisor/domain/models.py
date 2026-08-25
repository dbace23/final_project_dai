from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CustomerFeatures:
    age: int
    job: str
    marital: str
    education: str
    has_default: str
    has_housing_loan: str
    has_personal_loan: str
    contact: str
    campaign: int
    pdays: int
    previous: int
    poutcome: str
    emp_var_rate: float
    cons_price_idx: float
    cons_conf_idx: float
    euribor3m: float
    nr_employed: float

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class PredictionResult:
    predicted_subscribed: bool
    probability: float
    priority: str
    model: str


@dataclass(frozen=True)
class RetrievedSource:
    document_id: str
    document_name: str
    page: int | None
    chunk_id: str
    content: str
    distance: float


@dataclass(frozen=True)
class AdvisorRequest:
    customer: CustomerFeatures
    question: str


@dataclass(frozen=True)
class AdvisorResult:
    prediction: PredictionResult
    answer: str
    provider: str
    model: str
    retrieval_used: bool
    sources: list[RetrievedSource] = field(default_factory=list)
