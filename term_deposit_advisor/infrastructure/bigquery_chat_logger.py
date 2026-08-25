from uuid import uuid4

from google.cloud import bigquery

from term_deposit_advisor.config import AppConfig
from term_deposit_advisor.domain.models import AdvisorResult
from term_deposit_advisor.infrastructure.chat_logging import (
    serialize_retrieved_sources,
)


class BigQueryChatLogger:
    """Append-only interaction and feedback logging."""

    def __init__(self, client: bigquery.Client, config: AppConfig) -> None:
        self._client = client
        self._logs_table = config.table_id(config.chat_logs_table)
        self._feedback_table = config.table_id(config.chat_feedback_table)

    def log_interaction(
        self,
        *,
        email: str,
        question: str,
        result: AdvisorResult,
    ) -> str:
        interaction_id = str(uuid4())
        sql = f"""
        INSERT INTO `{self._logs_table}` (
          interaction_id,
          email,
          module,
          question,
          answer,
          provider,
          llm_model,
          ml_model,
          subscription_probability,
          predicted_subscribed,
          retrieval_used,
          retrieved_sources_json,
          `datetime`
        )
        VALUES (
          @interaction_id,
          @email,
          'banking',
          @question,
          @answer,
          @provider,
          @llm_model,
          @ml_model,
          @subscription_probability,
          @predicted_subscribed,
          @retrieval_used,
          @retrieved_sources_json,
          CURRENT_DATETIME('Asia/Jakarta')
        )
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "interaction_id", "STRING", interaction_id
                ),
                bigquery.ScalarQueryParameter("email", "STRING", email),
                bigquery.ScalarQueryParameter("question", "STRING", question),
                bigquery.ScalarQueryParameter("answer", "STRING", result.answer),
                bigquery.ScalarQueryParameter("provider", "STRING", result.provider),
                bigquery.ScalarQueryParameter("llm_model", "STRING", result.model),
                bigquery.ScalarQueryParameter(
                    "ml_model", "STRING", result.prediction.model
                ),
                bigquery.ScalarQueryParameter(
                    "subscription_probability",
                    "FLOAT64",
                    result.prediction.probability,
                ),
                bigquery.ScalarQueryParameter(
                    "predicted_subscribed",
                    "BOOL",
                    result.prediction.predicted_subscribed,
                ),
                bigquery.ScalarQueryParameter(
                    "retrieval_used", "BOOL", result.retrieval_used
                ),
                bigquery.ScalarQueryParameter(
                    "retrieved_sources_json",
                    "STRING",
                    serialize_retrieved_sources(result.sources),
                ),
            ]
        )
        self._client.query(sql, job_config=job_config).result()
        return interaction_id

    def log_feedback(
        self,
        *,
        interaction_id: str,
        email: str,
        feedback: str,
        comment: str,
    ) -> str:
        feedback_id = str(uuid4())
        sql = f"""
        INSERT INTO `{self._feedback_table}` (
          feedback_id,
          interaction_id,
          email,
          feedback,
          feedback_comment,
          `datetime`
        )
        VALUES (
          @feedback_id,
          @interaction_id,
          @email,
          @feedback,
          @feedback_comment,
          CURRENT_DATETIME('Asia/Jakarta')
        )
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("feedback_id", "STRING", feedback_id),
                bigquery.ScalarQueryParameter(
                    "interaction_id", "STRING", interaction_id
                ),
                bigquery.ScalarQueryParameter("email", "STRING", email),
                bigquery.ScalarQueryParameter("feedback", "STRING", feedback),
                bigquery.ScalarQueryParameter(
                    "feedback_comment", "STRING", comment.strip()
                ),
            ]
        )
        self._client.query(sql, job_config=job_config).result()
        return feedback_id
