from dataclasses import dataclass

from google.cloud import bigquery

from term_deposit_advisor.config import AppConfig


DEFAULT_SYSTEM_PROMPT = """
You are the Term-Deposit Subscription Advisor for bank marketing and
call-centre staff. Never calculate, change, replace, or invent the supplied
BigQuery ML probability. Retrieve official documents before stating
bank-specific rates, fees, eligibility, maturity, withdrawal, penalties,
minimum placement, or policy. Cite retrieved evidence and say when the
evidence is insufficient.
""".strip()


@dataclass(frozen=True)
class BankingRuntimeConfig:
    model_id: str
    prediction_sql: str
    system_prompt: str
    additional_prompt: str


class BigQueryRuntimeConfigRepository:
    """Load active runtime SQL and prompts without requiring a deployment."""

    REQUIRED_KEYS = {
        "model_id",
        "prediction_sql",
        "system_prompt",
        "additional_prompt",
    }

    def __init__(self, client: bigquery.Client, config: AppConfig) -> None:
        self._client = client
        self._config = config
        self._table_id = config.creds_table_id(config.runtime_config_table)

    def _values(self, module: str) -> dict[str, str]:
        sql = f"""
        SELECT `type`, value
        FROM `{self._table_id}`
        WHERE module = @module
          AND is_active
        QUALIFY ROW_NUMBER() OVER (
          PARTITION BY module, `type`
          ORDER BY version DESC, `datetime` DESC
        ) = 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("module", "STRING", module)
            ]
        )
        rows = self._client.query(sql, job_config=job_config).result()
        return {row["type"]: row["value"] for row in rows}

    def banking(self) -> BankingRuntimeConfig:
        values = self._values("banking")
        missing = sorted(self.REQUIRED_KEYS - values.keys())
        if missing:
            raise RuntimeError(
                "Missing active banking runtime configuration: "
                + ", ".join(missing)
            )

        return BankingRuntimeConfig(
            model_id=values["model_id"].strip(),
            prediction_sql=values["prediction_sql"].strip(),
            system_prompt=values.get("system_prompt", DEFAULT_SYSTEM_PROMPT).strip(),
            additional_prompt=values.get("additional_prompt", "").strip(),
        )
