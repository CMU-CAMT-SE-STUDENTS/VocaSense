-- Required before deploying the recommendation API.
-- Adds the valid guest/member-without-baseline assessment state only.
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
