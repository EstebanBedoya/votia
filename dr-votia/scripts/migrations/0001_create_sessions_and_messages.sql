-- Sessions & messages: anonymous conversation threads plus their turns.
--
-- Backs the SessionStore port (infrastructure/store/sessions.py): session
-- identity, conversation history, and the counting the rate limiter needs.
-- RLS is enabled; only the service_role key (this server) reads or writes —
-- the anon role has no policies and is therefore denied by default.

create table if not exists public.sessions (
    id          uuid primary key default gen_random_uuid(),
    created_at  timestamptz not null default now()
);

create table if not exists public.messages (
    id          bigint generated always as identity primary key,
    session_id  uuid not null references public.sessions (id) on delete cascade,
    role        text not null check (role in ('user', 'assistant')),
    content     text not null,
    ip          text,
    created_at  timestamptz not null default now()
);

-- Rate-limit lookups count user turns in a trailing window, keyed by ip or by
-- session. Partial index on user turns keeps those counts cheap.
create index if not exists messages_ip_created_idx
    on public.messages (ip, created_at)
    where role = 'user';

create index if not exists messages_session_created_idx
    on public.messages (session_id, created_at);

alter table public.sessions enable row level security;
alter table public.messages enable row level security;
