import re


FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|TRUNCATE|CALL|EXPORT|LOAD)\b",
    re.IGNORECASE,
)
MODEL_ID = re.compile(
    r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"
)


def render_prediction_sql(template: str, model_id: str) -> str:
    if not MODEL_ID.fullmatch(model_id):
        raise RuntimeError("model_id in model_read is not a valid BigQuery model ID.")
    sql = template.replace("{{MODEL_ID}}", model_id).strip()
    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise RuntimeError("prediction_sql must start with SELECT or WITH.")
    if FORBIDDEN_SQL.search(sql):
        raise RuntimeError("prediction_sql contains a disallowed write operation.")
    return sql
