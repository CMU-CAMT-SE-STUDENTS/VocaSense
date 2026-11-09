-- Browser-side assessment saves need a verifiable owner for both members and
-- short-lived guests. A guest token is a bearer credential supplied only in
-- the X-Guest-Token request header; it is never accepted from a JSON body.
create schema if not exists private;

create or replace function private.can_access_recording_assessment(
  p_analysis_id bigint,
  p_guest_token text
)
returns boolean
language sql
security definer
set search_path = ''
stable
as $$
  select exists (
    select 1
    from public.analysis as a
    left join public.guest_session as gs on gs.id = a.guest_session_id
    where a.id = p_analysis_id
      and (
        a.user_id = (select auth.uid())
        or (
          a.guest_session_id is not null
          -- Request headers are text. Cast the UUID column instead of the
          -- header, so malformed or absent tokens simply fail the check.
          and gs.guest_token::text = p_guest_token
          and gs.expires_at > now()
        )
      )
  );
$$;

revoke all on function private.can_access_recording_assessment(bigint, text) from public;
grant usage on schema private to anon, authenticated;
grant execute on function private.can_access_recording_assessment(bigint, text) to anon, authenticated;

alter table public.recording_assessment enable row level security;
grant select, insert, update on public.recording_assessment to anon, authenticated;

-- The same predicate is used for all required operations. This is necessary
-- for an upsert: PostgREST first reads the conflicting row, then updates it.
drop policy if exists "assessment owner can select" on public.recording_assessment;
drop policy if exists "assessment owner can insert" on public.recording_assessment;
drop policy if exists "assessment owner can update" on public.recording_assessment;

create policy "assessment owner can select"
on public.recording_assessment
for select
to anon, authenticated
using (
  (select private.can_access_recording_assessment(
    analysis_id,
    coalesce(current_setting('request.headers', true), '{}')::jsonb ->> 'x-guest-token'
  ))
);

create policy "assessment owner can insert"
on public.recording_assessment
for insert
to anon, authenticated
with check (
  (select private.can_access_recording_assessment(
    analysis_id,
    coalesce(current_setting('request.headers', true), '{}')::jsonb ->> 'x-guest-token'
  ))
);

create policy "assessment owner can update"
on public.recording_assessment
for update
to anon, authenticated
using (
  (select private.can_access_recording_assessment(
    analysis_id,
    coalesce(current_setting('request.headers', true), '{}')::jsonb ->> 'x-guest-token'
  ))
with check (
  (select private.can_access_recording_assessment(
    analysis_id,
    coalesce(current_setting('request.headers', true), '{}')::jsonb ->> 'x-guest-token'
  ))
);
