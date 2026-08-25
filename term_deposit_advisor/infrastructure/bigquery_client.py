from google.cloud import bigquery


def create_bigquery_client(project_id: str) -> bigquery.Client:
    """
    Local: Application Default Credentials.
    Cloud Run: attached runtime service account.
    """
    return bigquery.Client(project=project_id)
