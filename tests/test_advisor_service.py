import unittest

from term_deposit_advisor.application.advisor_service import AnalyzeCustomerUseCase
from term_deposit_advisor.domain.models import (
    AdvisorRequest,
    CustomerFeatures,
    PredictionResult,
    RetrievedSource,
)


CUSTOMER = CustomerFeatures(
    age=42,
    job="management",
    marital="married",
    education="university.degree",
    has_default="no",
    has_housing_loan="yes",
    has_personal_loan="no",
    contact="cellular",
    campaign=1,
    pdays=999,
    previous=0,
    poutcome="nonexistent",
    emp_var_rate=1.1,
    cons_price_idx=93.2,
    cons_conf_idx=-42.0,
    euribor3m=4.1,
    nr_employed=5191.0,
)


class FakePredictor:
    def predict(self, customer):
        return PredictionResult(True, 0.78, "High", "test.model")


class FakeSearch:
    def search(self, question, top_k=5):
        return [RetrievedSource("d1", "Terms", 7, "c1", "Evidence", 0.1)]


class FakeLLM:
    provider_name = "Fake"
    model_name = "fake-model"

    def answer(self, *, customer, prediction, question, document_search):
        sources = document_search.search(question)
        return "Answer", True, sources


class AnalyzeCustomerUseCaseTest(unittest.TestCase):
    def test_orchestrates_prediction_and_advisor(self):
        use_case = AnalyzeCustomerUseCase(FakePredictor(), FakeSearch(), FakeLLM())
        result = use_case.execute(AdvisorRequest(CUSTOMER, "Question"))

        self.assertAlmostEqual(result.prediction.probability, 0.78)
        self.assertEqual(result.answer, "Answer")
        self.assertTrue(result.retrieval_used)
        self.assertEqual(result.sources[0].page, 7)


if __name__ == "__main__":
    unittest.main()
