-- FRANTSAY V2 — sessions persistantes côté serveur
-- Le navigateur ne reçoit qu'un identifiant opaque de session.
-- Le refresh token Supabase reste chiffré dans PostgreSQL.

create table if not exists public.app_sessions (
    id uuid primary key default gen_random_uuid(),
    session_id_hash text not null unique,
    auth_user_id uuid not null,
    refresh_token_enc text not null,
    created_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    expires_at timestamptz not null
);

create index if not exists app_sessions_auth_user_id_idx
    on public.app_sessions(auth_user_id);

create index if not exists app_sessions_expires_at_idx
    on public.app_sessions(expires_at);

alter table public.app_sessions enable row level security;

-- Aucun accès direct depuis le navigateur.
-- FRANTSAY utilise uniquement la service-role key côté serveur.

-- Nettoyage des sessions expirées (à exécuter périodiquement si souhaité) :
-- delete from public.app_sessions where expires_at < now();
