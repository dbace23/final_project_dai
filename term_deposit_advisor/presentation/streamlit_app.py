import os

import streamlit as st

from term_deposit_advisor.bootstrap import build_use_case
from term_deposit_advisor.config import AppConfig
from term_deposit_advisor.domain.models import AdvisorRequest, CustomerFeatures
from term_deposit_advisor.infrastructure.bigquery_auth import BigQueryAuthGateway
from term_deposit_advisor.infrastructure.bigquery_chat_logger import (
    BigQueryChatLogger,
)
from term_deposit_advisor.infrastructure.bigquery_chunks import BigQueryChunkRepository
from term_deposit_advisor.infrastructure.document_chunking import (
    extract_pdf_chunks,
    safe_document_id,
)
from term_deposit_advisor.infrastructure.bigquery_client import create_bigquery_client


MODULE_LABELS = {
    "banking": "Banking Advisor",
    "chunker": "Document Chunker",
}


@st.cache_resource
def get_config() -> AppConfig:
    return AppConfig.from_env()


@st.cache_resource
def get_bigquery_client(project_id: str):
    return create_bigquery_client(project_id)


def render_login(auth_gateway: BigQueryAuthGateway) -> bool:
    if st.session_state.get("authenticated_user"):
        return True

    st.title("🏦 Term-Deposit AI")
    st.write("Sign in to open the modules assigned to your account.")
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Log in", type="primary", use_container_width=True
        )

    if submitted:
        try:
            user = auth_gateway.authenticate(email, password)
            if user is None:
                st.error("Email or password is incorrect.")
            elif not user.modules:
                st.error("This account has no assigned modules.")
            else:
                st.session_state["authenticated_user"] = {
                    "email": user.email,
                    "modules": list(user.modules),
                }
                st.rerun()
        except Exception as exc:
            st.error("Login could not be completed. Check the users table and service account permissions.")
            st.exception(exc)
    return False


def render_module_navigation() -> tuple[str, str]:
    user = st.session_state["authenticated_user"]
    allowed = [module for module in user["modules"] if module in MODULE_LABELS]
    if not allowed:
        st.error("None of the assigned modules are available in this app.")
        st.stop()

    with st.sidebar:
        st.write(f"Signed in as **{user['email']}**")
        labels = [MODULE_LABELS[module] for module in allowed]
        selected_label = st.radio("Module", labels)
        if st.button("Log out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    selected_module = allowed[labels.index(selected_label)]
    return selected_module, user["email"]


def render_settings(config: AppConfig) -> tuple[str, str, str | None, str | None]:
    with st.sidebar:
        st.divider()
        st.header("Advisor settings")
        provider = st.selectbox("AI provider", ["Gemini", "OpenRouter"])

        gemini_auth_mode = "Vertex AI / ADC"
        gemini_api_key = None
        openrouter_api_key = None

        if provider == "Gemini":
            gemini_auth_mode = st.radio(
                "Gemini authentication",
                ["Vertex AI / ADC", "Gemini API key"],
            )
            st.caption(f"Model: {config.gemini_model}")
            if gemini_auth_mode == "Gemini API key":
                gemini_api_key = st.text_input(
                    "Gemini API key",
                    value=os.getenv("GEMINI_API_KEY", ""),
                    type="password",
                )
        else:
            openrouter_api_key = st.text_input(
                "OpenRouter API key",
                value=os.getenv("OPENROUTER_API_KEY", ""),
                type="password",
            )
            st.caption(f"Model: {config.openrouter_model}")

        with st.expander("Backend configuration"):
            st.code(
                "\n".join(
                    [
                        f"Project: {config.project_id}",
                        f"Dataset: {config.dataset_id}",
                        f"Project config dataset: {config.creds_dataset_id}",
                        f"Runtime config: {config.creds_table_id(config.runtime_config_table)}",
                        f"Embedding model: {config.embed_model}",
                        f"RAG table: {config.rag_table}",
                    ]
                ),
                language="text",
            )

    return provider, gemini_auth_mode, gemini_api_key, openrouter_api_key


def render_customer_form() -> tuple[CustomerFeatures, str, bool]:
    with st.form("advisor_form"):
        st.subheader("Customer inputs")
        c1, c2, c3 = st.columns(3)

        with c1:
            age = st.number_input("Age", 18, 100, 42)
            job = st.selectbox(
                "Job",
                [
                    "management", "admin.", "blue-collar", "entrepreneur",
                    "housemaid", "retired", "self-employed", "services",
                    "student", "technician", "unemployed", "unknown",
                ],
            )
            marital = st.selectbox(
                "Marital status", ["married", "single", "divorced", "unknown"]
            )
            education = st.selectbox(
                "Education",
                [
                    "university.degree", "high.school", "basic.9y",
                    "professional.course", "basic.4y", "basic.6y",
                    "illiterate", "unknown",
                ],
            )
            has_default = st.selectbox("Credit default", ["no", "yes", "unknown"])

        with c2:
            housing = st.selectbox("Housing loan", ["yes", "no", "unknown"])
            personal_loan = st.selectbox("Personal loan", ["no", "yes", "unknown"])
            contact = st.selectbox("Contact type", ["cellular", "telephone"])
            campaign = st.number_input("Campaign contacts", min_value=0, value=1)
            pdays = st.number_input("Days since previous contact", min_value=0, value=999)
            previous = st.number_input("Previous contacts", min_value=0, value=0)
            poutcome = st.selectbox(
                "Previous outcome", ["nonexistent", "failure", "success"]
            )

        with c3:
            emp_var_rate = st.number_input(
                "Employment variation rate", value=1.1, format="%.3f"
            )
            cons_price_idx = st.number_input(
                "Consumer price index", value=93.2, format="%.3f"
            )
            cons_conf_idx = st.number_input(
                "Consumer confidence index", value=-42.0, format="%.3f"
            )
            euribor3m = st.number_input(
                "Euribor 3 month", value=4.1, format="%.3f"
            )
            nr_employed = st.number_input(
                "Number employed", value=5191.0, format="%.1f"
            )

        st.subheader("Question")
        question = st.text_area(
            "What would you like the advisor to answer?",
            value=(
                "Should I prioritize this customer, and what should I tell "
                "them if they ask about the rules for term deposit accounts?"
            ),
            height=110,
        )
        submitted = st.form_submit_button(
            "Predict + Ask Advisor", type="primary", use_container_width=True
        )

    customer = CustomerFeatures(
        age=int(age),
        job=job,
        marital=marital,
        education=education,
        has_default=has_default,
        has_housing_loan=housing,
        has_personal_loan=personal_loan,
        contact=contact,
        campaign=int(campaign),
        pdays=int(pdays),
        previous=int(previous),
        poutcome=poutcome,
        emp_var_rate=float(emp_var_rate),
        cons_price_idx=float(cons_price_idx),
        cons_conf_idx=float(cons_conf_idx),
        euribor3m=float(euribor3m),
        nr_employed=float(nr_employed),
    )
    return customer, question, submitted


def render_result(result) -> None:
    left, right = st.columns([0.8, 1.5])
    with left:
        st.subheader("Prediction")
        st.metric("Subscription probability", f"{result.prediction.probability:.1%}")
        st.metric("Outreach priority", result.prediction.priority)
        st.metric(
            "Predicted class",
            "Likely to subscribe"
            if result.prediction.predicted_subscribed
            else "Unlikely to subscribe",
        )
        st.caption("Calculated by BigQuery ML; not generated by the LLM.")

    with right:
        st.subheader("AI Advisor")
        st.markdown(result.answer)
        st.caption(
            f"{result.provider} · {result.model} · "
            + ("BigQuery RAG used" if result.retrieval_used else "No RAG retrieval")
        )

    if result.sources:
        st.subheader("Retrieved sources")
        unique = {
            (source.document_name, source.page, source.chunk_id): source
            for source in result.sources
        }
        for source in unique.values():
            page = f"page {source.page}" if source.page is not None else "page unknown"
            with st.expander(f"{source.document_name} — {page} — {source.chunk_id}"):
                st.write(source.content)
                st.caption(f"COSINE vector distance: {source.distance:.4f}")


def render_feedback(
    logger: BigQueryChatLogger,
    *,
    interaction_id: str,
    user_email: str,
) -> None:
    state_key = f"feedback_submitted_{interaction_id}"
    if st.session_state.get(state_key):
        st.success("Feedback recorded. Thank you.")
        return

    st.subheader("Feedback")
    with st.form(f"feedback_form_{interaction_id}"):
        feedback_label = st.radio(
            "Was this answer helpful?",
            ["Helpful", "Not helpful"],
            horizontal=True,
        )
        comment = st.text_area(
            "Comment (optional)",
            placeholder="What was useful, missing, or incorrect?",
        )
        submitted = st.form_submit_button("Submit feedback")

    if submitted:
        try:
            logger.log_feedback(
                interaction_id=interaction_id,
                email=user_email,
                feedback=(
                    "helpful" if feedback_label == "Helpful" else "not_helpful"
                ),
                comment=comment,
            )
            st.session_state[state_key] = True
            st.success("Feedback recorded. Thank you.")
        except Exception as exc:
            st.error("Feedback could not be logged.")
            st.exception(exc)


def render_banking(config: AppConfig, bq_client, user_email: str) -> None:
    st.title("🏦 Term-Deposit Subscription Advisor")
    st.write(
        "BigQuery ML calculates subscription probability. The selected LLM "
        "explains it and retrieves official product documents when needed."
    )
    st.caption(
        "The active model, prediction SQL, system prompt, and additional prompt "
        "are loaded from BigQuery for every analysis."
    )

    provider, gemini_auth_mode, gemini_api_key, openrouter_api_key = (
        render_settings(config)
    )
    customer, question, submitted = render_customer_form()
    logger = BigQueryChatLogger(bq_client, config)

    if submitted:
        st.session_state.pop("latest_analysis", None)
        try:
            use_case = build_use_case(
                config=config,
                bq_client=bq_client,
                provider=provider,
                gemini_auth_mode=gemini_auth_mode,
                gemini_api_key=gemini_api_key,
                openrouter_api_key=openrouter_api_key,
            )
            with st.status("Running analysis...", expanded=True) as status:
                st.write("Loading runtime configuration and running BigQuery ML...")
                result = use_case.execute(
                    AdvisorRequest(customer=customer, question=question)
                )
                st.write("Saving the answer and retrieved reads to the audit log...")
                interaction_id = logger.log_interaction(
                    email=user_email,
                    question=question,
                    result=result,
                )
                status.update(
                    label="Analysis complete", state="complete", expanded=False
                )
            st.session_state["latest_analysis"] = {
                "result": result,
                "interaction_id": interaction_id,
            }
        except Exception as exc:
            st.exception(exc)

    latest = st.session_state.get("latest_analysis")
    if latest:
        render_result(latest["result"])
        render_feedback(
            logger,
            interaction_id=latest["interaction_id"],
            user_email=user_email,
        )


def render_chunker(config: AppConfig, bq_client, user_email: str) -> None:
    st.title("📄 Document Chunker")
    st.write(
        "Upload a PDF, extract its text page by page, create overlapping chunks, "
        "preview them, and load them into BigQuery."
    )

    uploaded = st.file_uploader("PDF document", type=["pdf"])
    if uploaded is None:
        st.info("Upload a PDF to configure and preview its chunks.")
        return

    default_id = safe_document_id(uploaded.name)
    c1, c2 = st.columns(2)
    with c1:
        document_id = st.text_input(
            "Document ID",
            value=default_id,
            key=f"document_id_{uploaded.name}",
        ).strip()
        document_name = st.text_input(
            "Document name",
            value=uploaded.name.rsplit(".", 1)[0].replace("_", " ").title(),
            key=f"document_name_{uploaded.name}",
        ).strip()
        source_uri = st.text_input(
            "Source URI (optional)",
            placeholder="gs://bucket/path/file.pdf or public URL",
        ).strip()
    with c2:
        chunk_size = int(
            st.number_input(
                "Chunk size (characters)", min_value=100, max_value=10000, value=1200
            )
        )
        overlap = int(
            st.number_input(
                "Overlap (characters)",
                min_value=0,
                max_value=max(0, chunk_size - 1),
                value=min(200, chunk_size - 1),
            )
        )
        st.text_input(
            "Destination table",
            value=config.creds_table_id(config.chunks_table),
            disabled=True,
        )

    if st.button("Generate preview", type="primary", use_container_width=True):
        try:
            with st.spinner("Extracting and chunking PDF..."):
                chunks = extract_pdf_chunks(
                    uploaded.getvalue(),
                    document_id=document_id,
                    document_name=document_name,
                    source_uri=source_uri,
                    created_by=user_email,
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
            st.session_state["chunker_preview"] = {
                "filename": uploaded.name,
                "document_id": document_id,
                "chunks": chunks,
            }
        except Exception as exc:
            st.exception(exc)

    preview = st.session_state.get("chunker_preview")
    if not preview or preview["filename"] != uploaded.name:
        return

    chunks = preview["chunks"]
    st.success(f"Created {len(chunks):,} chunks.")
    st.dataframe(
        [
            {
                "page": chunk.page,
                "chunk_id": chunk.chunk_id,
                "characters": len(chunk.content),
                "content": chunk.content,
            }
            for chunk in chunks[:100]
        ],
        use_container_width=True,
        hide_index=True,
    )
    if len(chunks) > 100:
        st.caption("Preview shows the first 100 chunks.")

    st.warning(
        "Loading replaces existing rows with the same document_id, then inserts "
        "this preview."
    )
    if st.button("Load chunks to BigQuery", use_container_width=True):
        try:
            with st.spinner("Loading chunks to BigQuery..."):
                count = BigQueryChunkRepository(bq_client, config).replace_document(
                    preview["document_id"], chunks
                )
            st.success(
                f"Loaded {count:,} chunks into "
                f"{config.creds_table_id(config.chunks_table)}."
            )
        except Exception as exc:
            st.exception(exc)


def main() -> None:
    st.set_page_config(
        page_title="Term-Deposit AI",
        page_icon="🏦",
        layout="wide",
    )
    config = get_config()
    bq_client = get_bigquery_client(config.project_id)
    if not render_login(BigQueryAuthGateway(bq_client, config)):
        return

    module, user_email = render_module_navigation()
    if module == "banking":
        render_banking(config, bq_client, user_email)
    elif module == "chunker":
        render_chunker(config, bq_client, user_email)
