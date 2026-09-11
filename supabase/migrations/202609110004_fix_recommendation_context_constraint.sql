-- The deployed initial schema named its context check
-- recommendation_context_type_valid, not recommendation_context_type_check.
-- Keep exactly one context rule so guest v2 can use analysis_assessment.
ALTER TABLE public.recommendation
DROP CONSTRAINT IF EXISTS recommendation_context_type_valid;

ALTER TABLE public.recommendation
DROP CONSTRAINT IF EXISTS recommendation_context_type_check;

ALTER TABLE public.recommendation
ADD CONSTRAINT recommendation_context_type_check
CHECK (
  context_type IN (
    'analysis_only',
    'analysis_baseline',
    'analysis_assessment',
    'analysis_baseline_assessment'
  )
);
