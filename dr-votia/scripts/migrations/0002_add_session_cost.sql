-- Per-session OpenRouter spend.
--
-- Adds a running USD total to each session and an atomic increment function the
-- SessionStore calls after every chat turn (add_cost). Doing the add in Postgres
-- avoids a read-modify-write race between concurrent turns of the same session.

alter table public.sessions
    add column if not exists total_cost_usd numeric(12, 6) not null default 0;

-- Atomically add p_delta to the session's running spend and return the new
-- total in a single round-trip. SECURITY DEFINER so the service_role caller runs
-- it under the owner; RLS on sessions still gates which rows exist.
create or replace function public.increment_session_cost(
    p_session_id uuid,
    p_delta numeric
) returns numeric
language sql
as $$
    update public.sessions
       set total_cost_usd = total_cost_usd + p_delta
     where id = p_session_id
    returning total_cost_usd;
$$;
