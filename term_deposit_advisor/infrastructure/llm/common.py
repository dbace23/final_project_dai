from term_deposit_advisor.domain.models import CustomerFeatures, PredictionResult


def build_user_context(
    customer: CustomerFeatures,
    prediction: PredictionResult,
    question: str,
) -> str:
    return f"""
CURRENT CUSTOMER
Age: {customer.age}
Job: {customer.job}
Marital status: {customer.marital}
Education: {customer.education}
Credit default: {customer.has_default}
Housing loan: {customer.has_housing_loan}
Personal loan: {customer.has_personal_loan}
Contact type: {customer.contact}
Contacts this campaign: {customer.campaign}
Days since previous contact: {customer.pdays}
Previous contacts: {customer.previous}
Previous campaign outcome: {customer.poutcome}
Employment variation rate: {customer.emp_var_rate}
Consumer price index: {customer.cons_price_idx}
Consumer confidence index: {customer.cons_conf_idx}
Euribor 3 month: {customer.euribor3m}
Number employed: {customer.nr_employed}

BIGQUERY ML RESULT
Predicted subscription: {prediction.predicted_subscribed}
Subscription probability: {prediction.probability:.2%}
Outreach priority: {prediction.priority}
Model: {prediction.model}

STAFF QUESTION
{question}
""".strip()


def combine_system_prompts(system_prompt: str, additional_prompt: str) -> str:
    if not additional_prompt.strip():
        return system_prompt.strip()
    return (
        f"{system_prompt.strip()}\n\n"
        f"ADDITIONAL ACTIVE INSTRUCTIONS\n{additional_prompt.strip()}"
    )


TOOL_DESCRIPTION = (
    "Search the bank's official term-deposit documents. Use this for "
    "bank-specific rates, fees, eligibility, maturity, withdrawal, penalties, "
    "minimum placement, or other product conditions."
)
