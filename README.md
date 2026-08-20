# FRANTSAY 🇲🇬

Application Streamlit d'apprentissage du français.

## Stack

- Python / Streamlit
- Supabase Auth (e-mail + mot de passe)
- PostgreSQL / Supabase
- Gemini
- gTTS

## Sécurité

Les secrets ne sont pas stockés dans GitHub.

Le fichier `.streamlit/secrets.toml` doit être configuré dans Streamlit Cloud.

Variables nécessaires :

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (clé Publishable `sb_publishable_...`)
- `SUPABASE_SERVICE_ROLE_KEY` (clé Secret `sb_secret_...`)
- `GEMINI_API_KEY`
- `SESSION_ENCRYPTION_KEY`

## Base de données

La table `public.app_sessions` doit être créée avec `schema_auth_sessions.sql`.
