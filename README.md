# Links
**ppt**: https://docs.google.com/presentation/d/13HbRZhmr1Bg0hc_kEEyqjQHmkGunCDlK3Kj5id-Lt9I/edit?slide=id.g3fac66cf20a_0_0#slide=id.g3fac66cf20a_0_0
**url**:https://term-deposit-advisor-3rfhu5n4pq-as.a.run.app/

note: 
1. docker will run tapi butuh akses untuk ke DB bq
2. url will be live until 09/10/2026
   
# Term-Deposit AI

Streamlit app with two BigQuery-authorized modules:

- **Banking Advisor** — BigQuery ML prediction plus agentic document retrieval.
- **Document Chunker** — PDF upload, page extraction, overlapping chunk preview,
  and loading to BigQuery.

## 1. Create the BigQuery tables and seed rows

Run [sql/setup_bigquery.sql](sql/setup_bigquery.sql) in the BigQuery editor.
It creates:

- `cool-benefit-286000.project_creds.users`
- `cool-benefit-286000.project_creds.model_read`
- `cool-benefit-286000.project_creds.document_chunks`
- `cool-benefit-286000.bankData_final_project.ai_chat_logs`
- `cool-benefit-286000.bankData_final_project.ai_chat_feedback`

The app uses two datasets deliberately:

- `project_creds`: users, runtime model/prompt configuration, and document chunks.
- `bankData_final_project`: BigQuery ML/RAG resources and AI audit logs.

The script creates all tables first, then uses `INSERT INTO` for seed rows. It
does not use `MERGE` for users or runtime configuration. Additional copy-paste
inserts are in [sql/dml_examples.sql](sql/dml_examples.sql).

The seeded login is:

- Email: `halim.iskandar@gmail.com`
- Password: `123456`
- Modules: `chunker, banking`

The user fields are `email`, `password_hash`, `module_access`, and `is_active`,
with `created_at` and `updated_at`. Login compares
`password_hash = TO_HEX(SHA256(@password))`; plaintext passwords are not stored.
For a public production app, use a deliberately slow salted password hash or
managed OIDC/IAP authentication.

## 2. Runtime model SQL and prompts

The Banking Advisor reads these active `model_read.type` values at analysis
time. Each row also records the editor `email` and Jakarta `datetime`:

| Key | Purpose |
| --- | --- |
| `model_id` | Fully qualified BigQuery ML model ID |
| `prediction_sql` | Parameterized, read-only ML.PREDICT query |
| `system_prompt` | Main LLM rules |
| `additional_prompt` | Extra system-level instructions combined at runtime |

This means a compatible model, prediction query, or prompt can be changed
without rebuilding or redeploying the app. The SQL must remain read-only,
start with `SELECT` or `WITH`, use `{{MODEL_ID}}` for the model identifier,
and return:

- `predicted_subscribed`
- `predicted_subscribed_probs`

Customer values are passed as named BigQuery parameters. The app reads the
active model's feature schema at runtime so STRING/FLOAT64/INT64 changes do not
require source-code changes when the feature names remain the same.

New versions are appended with `INSERT INTO`; the highest active `version` for
each `module` + `type` is used.

## 3. AI interaction and feedback logs

Every successful AI analysis appends one row to `ai_chat_logs` containing:

- Authenticated email and Jakarta datetime.
- Question and generated answer.
- LLM provider/model and BigQuery ML model.
- Prediction, probability, and whether retrieval was used.
- The complete retrieved read/chunk metadata and content as JSON.

The UI then displays Helpful / Not helpful feedback plus an optional comment.
Each submission appends a separate row to `ai_chat_feedback`, linked by
`interaction_id`, with its own email and Jakarta datetime. No original chat log
is updated or overwritten.

## 4. Chunker behavior

The Chunker is based on the supplied `extract_and_chunk (2).py` logic:

1. Read uploaded PDF bytes with pypdf.
2. Extract text page by page.
3. Split text with configurable character size and overlap.
4. Preview the first 100 chunks.
5. Delete existing rows for the same `document_id`.
6. Insert the previewed chunks into `document_chunks`.

It uploads chunks only. Your existing embedding pipeline can read
`document_chunks` and refresh `document_embeddings`.

## 5. Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
gcloud auth application-default login
streamlit run app.py
```

Copy `.env.example` values into your environment as needed. Cloud Run should
use its attached service account rather than a local credentials file.

## 6. Required Google Cloud access

The runtime service account needs:

- BigQuery Job User on the project.
- Read access to `users`, `model_read`, the ML model, embedding model, and
  `document_embeddings`.
- Read/write access to `document_chunks`.
- Insert access to `ai_chat_logs` and `ai_chat_feedback`.
- Vertex AI User when Gemini uses Vertex AI / ADC.

## 7. Test

```powershell
python -m unittest discover -s tests -v
```

The application tests use fakes and do not call Google Cloud or an LLM.

## Architecture

```text
Streamlit
  ├─ BigQuery users authentication
  ├─ Banking Advisor
  │    ├─ model_read runtime configuration
  │    ├─ BigQuery ML prediction
  │    ├─ Gemini/OpenRouter + BigQuery RAG
  │    └─ Append-only interaction + feedback logs
  └─ Document Chunker
       └─ PDF extraction + BigQuery document_chunks
```
