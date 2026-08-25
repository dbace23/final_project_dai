from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    project_id: str
    dataset_id: str
    creds_dataset_id: str
    model_name: str
    embed_model: str
    rag_table: str
    vertex_location: str
    gemini_model: str
    openrouter_model: str
    openrouter_base_url: str
    users_table: str
    runtime_config_table: str
    chunks_table: str
    chat_logs_table: str
    chat_feedback_table: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            project_id=os.getenv("GCP_PROJECT_ID", "cool-benefit-286000"),
            dataset_id=os.getenv("BQ_DATASET_ID", "bankData_final_project"),
            creds_dataset_id=os.getenv("BQ_CREDS_DATASET_ID", "project_creds"),
            model_name=os.getenv("BQ_MODEL_NAME", "term_deposit_logistic_tuned"),
            embed_model=os.getenv("BQ_EMBED_MODEL", "embedding_model"),
            rag_table=os.getenv("BQ_RAG_TABLE", "document_embeddings"),
            vertex_location=os.getenv("VERTEX_LOCATION", "global"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", "google/gemini-2.5-flash"
            ),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            users_table=os.getenv("BQ_USERS_TABLE", "users"),
            runtime_config_table=os.getenv("BQ_RUNTIME_CONFIG_TABLE", "model_read"),
            chunks_table=os.getenv("BQ_CHUNKS_TABLE", "document_chunks"),
            chat_logs_table=os.getenv("BQ_CHAT_LOGS_TABLE", "ai_chat_logs"),
            chat_feedback_table=os.getenv(
                "BQ_CHAT_FEEDBACK_TABLE", "ai_chat_feedback"
            ),
        )

    def table_id(self, table_name: str) -> str:
        return f"{self.project_id}.{self.dataset_id}.{table_name}"

    def creds_table_id(self, table_name: str) -> str:
        return f"{self.project_id}.{self.creds_dataset_id}.{table_name}"
