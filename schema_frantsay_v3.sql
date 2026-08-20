-- ============================================================
-- FRANTSAY V3 — Schema Supabase complet
-- "L'Ame de Madagascar" — Auth Email/MDP + Sessions persistantes
-- ============================================================

-- -----------------------------------------------------------
-- 1. Table des sessions persistantes cote serveur
-- Le navigateur ne recoit qu'un identifiant opaque de session.
-- Le refresh token Supabase reste chiffre dans PostgreSQL.
-- -----------------------------------------------------------

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

-- Aucun acces direct depuis le navigateur.
-- FRANTSAY utilise uniquement la service-role key cote serveur.

-- Nettoyage des sessions expirees (a executer periodiquement) :
-- delete from public.app_sessions where expires_at < now();


-- -----------------------------------------------------------
-- 2. Table des profils utilisateurs (public.users)
-- Lien avec auth.users via auth_user_id (CASCADE on delete)
-- Niveau pedagogique verrouille, progression stockee en JSON
-- -----------------------------------------------------------

create table if not exists public.users (
    id uuid primary key default gen_random_uuid(),
    auth_user_id uuid not null references auth.users(id) on delete cascade,
    email text not null,
    pseudo text,
    display_name text,
    level text not null check (level in ('College', 'Lycee', 'Universite')),
    score integer not null default 0,
    questions_done integer not null default 0,
    progress jsonb not null default '{"score": 0, "questions_done": 0}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Index pour rechercher rapidement par auth_user_id
create index if not exists users_auth_user_id_idx
    on public.users(auth_user_id);

-- Index pour rechercher par email (admin/debug uniquement)
create index if not exists users_email_idx
    on public.users(email);

-- Contrainte d'unicite : un seul profil par utilisateur auth
create unique index if not exists users_auth_user_id_unique
    on public.users(auth_user_id);

-- Trigger pour mettre a jour updated_at automatiquement
create or replace function update_users_modified_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language 'plpgsql';

drop trigger if exists update_users_modtime on public.users;
create trigger update_users_modtime
    before update on public.users
    for each row
    execute function update_users_modified_column();

-- RLS : aucun acces direct depuis le client (FRANTSAY utilise service-role)
alter table public.users enable row level security;

-- Politique de securite : seul le proprietaire peut voir/modifier son profil
-- (en cas d'acces client direct, bien que FRANTSAY n'utilise pas ce chemin)
create policy if not exists "Users can view own profile"
    on public.users for select
    using (auth.uid() = auth_user_id);

create policy if not exists "Users can update own profile"
    on public.users for update
    using (auth.uid() = auth_user_id);


-- -----------------------------------------------------------
-- 3. Vue admin (optionnelle) pour le monitoring
-- -----------------------------------------------------------

create or replace view public.user_stats as
select 
    u.id,
    u.display_name,
    u.level,
    u.score,
    u.questions_done,
    u.created_at,
    u.updated_at
from public.users u
order by u.score desc;


-- -----------------------------------------------------------
-- 4. Instructions de configuration Supabase Auth
-- -----------------------------------------------------------

-- Dans le dashboard Supabase :
-- 1. Authentication > Providers > Email : active "Enable Email Confirmations"
--    (desactive en dev si tu veux skipper la confirmation)
-- 2. Authentication > URL Configuration :
--    - Site URL : https://ton-app.streamlit.app
--    - Redirect URLs : https://ton-app.streamlit.app/**
-- 3. Settings > API :
--    - Copie Project URL -> SUPABASE_URL
--    - Copie anon/public key -> SUPABASE_ANON_KEY
--    - Copie service_role key -> SUPABASE_SERVICE_ROLE_KEY (NE JAMAIS EXPOSER)
