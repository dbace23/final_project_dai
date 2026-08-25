-- ================================================================
-- INSERT ANOTHER USER (same AstroUTM-style field names)
-- ================================================================
INSERT INTO `cool-benefit-286000.project_creds.users` (
  email, password_hash, module_access, is_active, created_at, updated_at
)
VALUES (
  'another.user@gmail.com',
  TO_HEX(SHA256('change-this-password')),
  'banking',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);

-- ================================================================
-- INSERT A NEW MODEL VERSION - NO APP DEPLOYMENT
-- ================================================================
INSERT INTO `cool-benefit-286000.project_creds.model_read` (
  module, `type`, value, version, is_active, email, `datetime`
)
SELECT
  'banking',
  'model_id',
  'cool-benefit-286000.bankData_final_project.new_model_name',
  COALESCE(MAX(version), 0) + 1,
  TRUE,
  'halim.iskandar@gmail.com',
  CURRENT_DATETIME('Asia/Jakarta')
FROM `cool-benefit-286000.project_creds.model_read`
WHERE module = 'banking' AND `type` = 'model_id';

-- ================================================================
-- INSERT A NEW ADDITIONAL PROMPT VERSION - NO APP DEPLOYMENT
-- ================================================================
INSERT INTO `cool-benefit-286000.project_creds.model_read` (
  module, `type`, value, version, is_active, email, `datetime`
)
SELECT
  'banking',
  'additional_prompt',
  'Respond in Bahasa Indonesia and finish with one recommended next action.',
  COALESCE(MAX(version), 0) + 1,
  TRUE,
  'halim.iskandar@gmail.com',
  CURRENT_DATETIME('Asia/Jakarta')
FROM `cool-benefit-286000.project_creds.model_read`
WHERE module = 'banking' AND `type` = 'additional_prompt';

-- ================================================================
-- APP PARAMETERIZED INSERT: AI INTERACTION + RETRIEVED READS
-- ================================================================
INSERT INTO `cool-benefit-286000.bankData_final_project.ai_chat_logs` (
  interaction_id, email, module, question, answer, provider, llm_model,
  ml_model, subscription_probability, predicted_subscribed, retrieval_used,
  retrieved_sources_json, `datetime`
)
VALUES (
  @interaction_id, @email, 'banking', @question, @answer, @provider,
  @llm_model, @ml_model, @subscription_probability, @predicted_subscribed,
  @retrieval_used, @retrieved_sources_json,
  CURRENT_DATETIME('Asia/Jakarta')
);

-- ================================================================
-- APP PARAMETERIZED INSERT: USER FEEDBACK
-- ================================================================
INSERT INTO `cool-benefit-286000.bankData_final_project.ai_chat_feedback` (
  feedback_id, interaction_id, email, feedback, feedback_comment, `datetime`
)
VALUES (
  @feedback_id, @interaction_id, @email, @feedback, @feedback_comment,
  CURRENT_DATETIME('Asia/Jakarta')
);
