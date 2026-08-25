from google.cloud import bigquery

PROJECT_ID = "cool-benefit-286000"
MODEL_ID = (
    "cool-benefit-286000."
    "bankData_final_project."
    "term_deposit_logistic_tuned"
)

client = bigquery.Client(project=PROJECT_ID)
model = client.get_model(MODEL_ID)

print(f"Model: {MODEL_ID}")
print()
print("Feature schema:")
print("-" * 45)

for field in model.feature_columns:
    type_kind = field.type.type_kind
    type_name = getattr(type_kind, "value", str(type_kind))
    print(f"{field.name:30} {type_name}")

print()
print("Label schema:")
print("-" * 45)

for field in model.label_columns:
    type_kind = field.type.type_kind
    type_name = getattr(type_kind, "value", str(type_kind))
    print(f"{field.name:30} {type_name}")
