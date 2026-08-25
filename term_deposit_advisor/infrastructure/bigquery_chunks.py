from dataclasses import asdict

from google.cloud import bigquery

from term_deposit_advisor.config import AppConfig
from term_deposit_advisor.infrastructure.document_chunking import DocumentChunk


class BigQueryChunkRepository:
    def __init__(self, client: bigquery.Client, config: AppConfig) -> None:
        self._client = client
        self.table_id = config.creds_table_id(config.chunks_table)

    def replace_document(self, document_id: str, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            raise ValueError("The PDF produced no text chunks.")

        delete_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("document_id", "STRING", document_id)
            ]
        )
        self._client.query(
            f"DELETE FROM `{self.table_id}` WHERE document_id = @document_id",
            job_config=delete_config,
        ).result()

        errors = self._client.insert_rows_json(
            self.table_id,
            [asdict(chunk) for chunk in chunks],
        )
        if errors:
            raise RuntimeError(f"BigQuery chunk upload failed: {errors}")
        return len(chunks)
