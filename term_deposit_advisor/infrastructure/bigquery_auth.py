from dataclasses import dataclass

from google.cloud import bigquery

from term_deposit_advisor.config import AppConfig


@dataclass(frozen=True)
class AuthenticatedUser:
    email: str
    modules: tuple[str, ...]


class BigQueryAuthGateway:
    """Authenticate Streamlit users against the configured BigQuery table."""

    def __init__(self, client: bigquery.Client, config: AppConfig) -> None:
        self._client = client
        self._table_id = config.creds_table_id(config.users_table)

    def authenticate(self, email: str, password: str) -> AuthenticatedUser | None:
        normalized_email = email.strip().lower()
        if not normalized_email or not password:
            return None

        sql = f"""
        SELECT email, module_access
        FROM `{self._table_id}`
        WHERE LOWER(email) = @email
          AND LOWER(password_hash) = LOWER(TO_HEX(SHA256(@password)))
          AND COALESCE(is_active, TRUE)
        QUALIFY ROW_NUMBER() OVER (
          PARTITION BY LOWER(email)
          ORDER BY updated_at DESC
        ) = 1
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", normalized_email),
                bigquery.ScalarQueryParameter("password", "STRING", password),
            ]
        )
        rows = list(self._client.query(sql, job_config=job_config).result())
        if not rows:
            return None

        modules = tuple(
            item.strip().lower()
            for item in (rows[0]["module_access"] or "").split(",")
            if item.strip()
        )
        return AuthenticatedUser(email=rows[0]["email"], modules=modules)
