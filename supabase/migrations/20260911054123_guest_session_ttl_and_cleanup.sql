-- Guest history is intentionally short lived.  Claimed analyses have their
-- guest_session_id cleared by the existing claim flow, so this cleanup only
-- removes data that was never transferred to a member account.
alter table public.guest_session
  alter column expires_at set default (now() + interval '10 minutes');

-- The cron job filters by expiry on every run; this keeps cleanup inexpensive
-- as the guest-session table grows.
create index if not exists guest_session_expires_at_idx
  on public.guest_session (expires_at);

-- `cron.schedule` replaces a job with the same name, making this migration
-- idempotent if it is applied to an environment where the job already exists.
select cron.schedule(
  'delete-expired-guest-sessions',
  '*/10 * * * *',
  $cron$
    delete from public.guest_session
    where expires_at <= now();
  $cron$
);
