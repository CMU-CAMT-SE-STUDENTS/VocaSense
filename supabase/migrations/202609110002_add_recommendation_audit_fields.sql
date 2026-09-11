-- Required before deploying the recommendation API.
-- Nullable at database level so existing recommendation rows remain valid.
-- New application-generated rows always populate all three columns.
ALTER TABLE public.recommendation
ADD COLUMN IF NOT EXISTS behavior_scores jsonb,
ADD COLUMN IF NOT EXISTS behavior_scoring_version character varying,
ADD COLUMN IF NOT EXISTS recommendation_rule_version character varying;

COMMENT ON COLUMN public.recommendation.behavior_scores IS
  'Derived deterministic category scores; raw questionnaire answers belong in snapshots.';
COMMENT ON COLUMN public.recommendation.behavior_scoring_version IS
  'Version of deterministic behavior scoring logic.';
COMMENT ON COLUMN public.recommendation.recommendation_rule_version IS
  'Version of deterministic recommendation candidate and ranking rules.';
