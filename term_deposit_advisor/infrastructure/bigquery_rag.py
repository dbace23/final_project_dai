from google.cloud import bigquery

from term_deposit_advisor.config import AppConfig
from term_deposit_advisor.domain.models import RetrievedSource


class BigQueryDocumentSearchGateway:
    def __init__(self, client: bigquery.Client, config: AppConfig) -> None:
        self._client = client
        self._config = config

    def search(self, question: str, top_k: int = 5) -> list[RetrievedSource]:
        top_k = max(1, min(int(top_k), 10))
        c = self._config

        # This intentionally matches the verified RAG query:
        # - embedding_model in bankData_final_project
        # - document_embeddings in bankData_final_project
        # - RETRIEVAL_QUERY
        # - COSINE distance
        sql = f"""
        WITH query_embedding AS (
          SELECT
            embedding
          FROM AI.GENERATE_EMBEDDING(
            MODEL `{c.project_id}.{c.dataset_id}.{c.embed_model}`,
            (
              SELECT
                @question AS content
            ),
            STRUCT(
              'RETRIEVAL_QUERY' AS task_type
            )
          )
        )

        SELECT
          base.document_id,
          base.document_name,
          base.page,
          base.chunk_id,
          base.content,
          distance
        FROM VECTOR_SEARCH(
          TABLE `{c.project_id}.{c.dataset_id}.{c.rag_table}`,
          'embedding',
          TABLE query_embedding,
          'embedding',
          top_k => {top_k},
          distance_type => 'COSINE'
        )
        ORDER BY distance
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("question", "STRING", question)
            ]
        )
        rows = list(self._client.query(sql, job_config=job_config).result())

        return [
            RetrievedSource(
                document_id=row["document_id"],
                document_name=row["document_name"],
                page=int(row["page"]) if row["page"] is not None else None,
                chunk_id=row["chunk_id"],
                content=row["content"],
                distance=float(row["distance"]),
            )
            for row in rows
        ]
