import json
from pathlib import Path
import unittest

from term_deposit_advisor.domain.models import RetrievedSource
from term_deposit_advisor.infrastructure.chat_logging import (
    serialize_retrieved_sources,
)
from term_deposit_advisor.infrastructure.document_chunking import (
    chunk_text,
    safe_document_id,
)
from term_deposit_advisor.infrastructure.runtime_sql import render_prediction_sql


class ChunkerTest(unittest.TestCase):
    def test_chunks_with_overlap(self):
        text = "a" * 80 + "b" * 40
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0], "a" * 80 + "b" * 20)
        self.assertEqual(chunks[1], "b" * 40)

    def test_rejects_invalid_overlap(self):
        with self.assertRaises(ValueError):
            chunk_text("content", chunk_size=100, overlap=100)

    def test_safe_document_id(self):
        self.assertEqual(
            safe_document_id("Term Deposit Terms (Final).pdf"),
            "term_deposit_terms_final",
        )


class RuntimePredictionSqlTest(unittest.TestCase):
    def test_renders_valid_model_identifier(self):
        sql = render_prediction_sql(
            "SELECT * FROM ML.PREDICT(MODEL `{{MODEL_ID}}`, (SELECT 1))",
            "cool-benefit-286000.bankData_final_project.model_v2",
        )
        self.assertIn("model_v2", sql)
        self.assertNotIn("{{MODEL_ID}}", sql)

    def test_rejects_write_sql(self):
        with self.assertRaises(RuntimeError):
            render_prediction_sql(
                "WITH x AS (SELECT 1) DELETE FROM dataset.table WHERE TRUE",
                "project.dataset.model",
            )


class ChatLoggingTest(unittest.TestCase):
    def test_serializes_the_retrieved_read(self):
        payload = serialize_retrieved_sources(
            [RetrievedSource("doc-1", "Terms", 3, "chunk-1", "Evidence", 0.12)]
        )
        parsed = json.loads(payload)
        self.assertEqual(parsed[0]["chunk_id"], "chunk-1")
        self.assertEqual(parsed[0]["content"], "Evidence")

    def test_setup_seed_is_insert_only(self):
        setup_sql = (
            Path(__file__).parents[1] / "sql" / "setup_bigquery.sql"
        ).read_text(encoding="utf-8")
        self.assertIn("INSERT INTO", setup_sql)
        self.assertNotIn("MERGE ", setup_sql.upper())
        self.assertIn("password_hash STRING", setup_sql)
        self.assertNotIn("password STRING", setup_sql)
        for table in ("users", "model_read", "document_chunks"):
            self.assertIn(
                f"cool-benefit-286000.project_creds.{table}", setup_sql
            )
            self.assertNotIn(
                f"cool-benefit-286000.bankData_final_project.{table}",
                setup_sql,
            )


if __name__ == "__main__":
    unittest.main()
