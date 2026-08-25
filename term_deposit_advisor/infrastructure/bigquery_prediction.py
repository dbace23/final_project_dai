from decimal import Decimal
from typing import Any

from google.cloud import bigquery

from term_deposit_advisor.config import AppConfig
from term_deposit_advisor.domain.models import CustomerFeatures, PredictionResult
from term_deposit_advisor.infrastructure.bigquery_runtime_config import (
    BigQueryRuntimeConfigRepository,
)
from term_deposit_advisor.infrastructure.runtime_sql import render_prediction_sql


class BigQueryPredictionGateway:
    """Run the active prediction SQL stored in BigQuery model_read."""

    SUPPORTED_TYPES = {
        "STRING",
        "INT64",
        "FLOAT64",
        "BOOL",
        "NUMERIC",
        "BIGNUMERIC",
    }

    def __init__(
        self,
        client: bigquery.Client,
        config: AppConfig,
        runtime_config: BigQueryRuntimeConfigRepository,
    ) -> None:
        self._client = client
        self._config = config
        self._runtime_config = runtime_config

    @staticmethod
    def _positive_probability(probabilities: Any) -> float:
        for item in probabilities:
            label = str(item["label"]).strip().lower()
            if label in {"1", "true", "yes"}:
                return float(item["prob"])
        raise RuntimeError(
            "Positive class not found in predicted_subscribed_probs: "
            f"{probabilities}"
        )

    def _query_parameters(
        self, customer: CustomerFeatures, model_id: str
    ) -> list[bigquery.ScalarQueryParameter]:
        values = customer.as_dict()
        model = self._client.get_model(model_id)
        feature_types: dict[str, str] = {}
        for field in model.feature_columns:
            if not field.name or field.type is None:
                continue
            kind = field.type.type_kind
            type_name = (
                str(getattr(kind, "value", None) or kind)
                .upper()
                .rsplit(".", 1)[-1]
            )
            if type_name not in self.SUPPORTED_TYPES:
                raise RuntimeError(
                    f"Unsupported BigQuery ML type for {field.name}: {type_name}"
                )
            feature_types[field.name] = type_name

        missing = sorted(set(feature_types) - set(values))
        if missing:
            raise RuntimeError(
                "The active model expects unsupported customer fields: "
                + ", ".join(missing)
            )

        def coerce(value: Any, type_name: str) -> Any:
            if type_name == "STRING":
                return str(value)
            if type_name == "INT64":
                return int(value)
            if type_name == "FLOAT64":
                return float(value)
            if type_name == "BOOL":
                return str(value).strip().lower() in {"true", "1", "yes", "y"}
            if type_name in {"NUMERIC", "BIGNUMERIC"}:
                return Decimal(str(value))
            return value

        return [
            bigquery.ScalarQueryParameter(
                name, type_name, coerce(values[name], type_name)
            )
            for name, type_name in feature_types.items()
        ]

    def predict(self, customer: CustomerFeatures) -> PredictionResult:
        runtime = self._runtime_config.banking()
        sql = render_prediction_sql(runtime.prediction_sql, runtime.model_id)
        rows = list(
            self._client.query(
                sql,
                job_config=bigquery.QueryJobConfig(
                    query_parameters=self._query_parameters(customer, runtime.model_id)
                ),
            ).result()
        )
        if not rows:
            raise RuntimeError("BigQuery ML returned no prediction.")

        row = rows[0]
        probability = self._positive_probability(row["predicted_subscribed_probs"])
        positive = str(row["predicted_subscribed"]).strip().lower() in {
            "1", "true", "yes"
        }
        priority = (
            "High" if probability >= 0.60
            else "Medium" if probability >= 0.30
            else "Low"
        )
        return PredictionResult(
            predicted_subscribed=positive,
            probability=probability,
            priority=priority,
            model=runtime.model_id,
        )
