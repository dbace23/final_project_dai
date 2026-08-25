#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-cool-benefit-286000}"
REGION="${REGION:-asia-southeast2}"
REPOSITORY="${REPOSITORY:-term-deposit-app}"
SERVICE="${SERVICE:-term-deposit-advisor}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:latest"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-term-deposit-advisor-sa@${PROJECT_ID}.iam.gserviceaccount.com}"

gcloud config set project "${PROJECT_ID}"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com bigquery.googleapis.com aiplatform.googleapis.com

gcloud artifacts repositories describe "${REPOSITORY}" --location="${REGION}" >/dev/null 2>&1 || \
gcloud artifacts repositories create "${REPOSITORY}" --repository-format=docker --location="${REGION}" --description="Term Deposit Advisor containers"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker build -t "${IMAGE}" .
docker push "${IMAGE}"

gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --port 8080 \
  --service-account "${SERVICE_ACCOUNT}" \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},BQ_DATASET_ID=bankData_final_project,BQ_MODEL_NAME=term_deposit_logistic_tuned,BQ_EMBED_MODEL=embedding_model,BQ_RAG_TABLE=document_embeddings,VERTEX_LOCATION=global"

gcloud run services describe "${SERVICE}" --region="${REGION}" --format="value(status.url)"
