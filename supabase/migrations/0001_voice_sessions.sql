-- VocaSense: voice_sessions table
-- Run this once in the Supabase SQL editor (Project → SQL Editor → New query)
-- for the project at https://beuyzslrgnealuddjbfu.supabase.co
--
-- Stores one row per completed voice analysis, saved by ResultView.vue right
-- after a member finishes a test, and read back by HistoryView.vue to draw
-- the Voice Health Score chart and the Record List.

create table if not exists public.voice_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  score smallint not null check (score >= 0 and score <= 100),
  risk text not null check (risk in ('low', 'moderate', 'high')),
  result_label text not null,
  metrics jsonb not null default '[]'::jsonb,
  recommendations jsonb not null default '[]'::jsonb
);

create index if not exists voice_sessions_user_id_created_at_idx
  on public.voice_sessions (user_id, created_at);

alter table public.voice_sessions enable row level security;

-- Members can only ever see/insert their own sessions.
drop policy if exists "Members can view their own voice sessions" on public.voice_sessions;
create policy "Members can view their own voice sessions"
  on public.voice_sessions for select
  using (auth.uid() = user_id);

drop policy if exists "Members can insert their own voice sessions" on public.voice_sessions;
create policy "Members can insert their own voice sessions"
  on public.voice_sessions for insert
  with check (auth.uid() = user_id);
