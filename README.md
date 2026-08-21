# FRANTSAY V4 — Refactoring Complet

## 🎯 Résumé des modifications

Cette version refactorise entièrement l'application FRANTSAY V3 en corrigeant 5 bugs critiques et en restructurant l'UI/UX.

---

## ✅ Corrections des 5 Bugs Critiques

### 1. Persistance de session (Bug F5)
**Problème** : `streamlit-cookies-controller` v0.0.4 perdait l'état au rafraîchissement.

**Solution** :
- Remplacement par `extra_streamlit_components.CookieManager` (plus robuste)
- Fallback sur `st.query_params` pour stocker le `frantsay_sid`
- Synchronisation automatique du token Supabase avec `st.session_state` au chargement
- Régénération du cookie à chaque restauration pour éviter l'expiration navigateur

### 2. Composants interactifs (Réactivité UI)
**Problème** : HTML/CSS brut (`st.markdown(..., unsafe_allow_html=True)`) brisait la liaison bidirectionnelle de Streamlit.

**Solution** :
- Suppression de la barre d'onglets horizontale HTML statique
- Remplacement par `st.segmented_control` (Streamlit natif) ou `st.radio` (fallback)
- Navigation "Ton Espace" entièrement gérée par le state Streamlit

### 3. Enregistreur vocal
**Problème** : Script JS injecté (`RECORDER_HTML_TEMPLATE`) avec manipulations DOM instables (`document.querySelector`).

**Solution** :
- Suppression complète du JS custom
- Intégration de `audio_recorder_streamlit` (bibliothèque standardisée)
- Composant robuste via `streamlit.components.v1` en fallback

### 4. Design immersif & Contraste (WCAG AAA)
**Problème** : Mode clair imposé + fonds SVG abstraits = mauvaise lisibilité.

**Solution** :
- Fond photographique HD (Baobabs Madagascar) via `background-image`
- Overlay CSS sombre semi-transparent (`rgba(26, 20, 16, 0.82)`)
- Cartes avec `backdrop-filter: blur(8px)` et fond semi-transparent (`rgba(255,255,255,0.92)`)
- Support thème sombre via `@media (prefers-color-scheme: dark)`

### 5. Optimisation performances (Mémoire & Cache)
**Problème** : Latence appels LLM + écriture fichiers audio sur disque.

**Solution** :
- `gTTS` génère directement en `io.BytesIO()` (pas de fichiers temporaires)
- `@st.cache_data(ttl=3600)` sur les fonctions d'appel Gemini
- `@st.cache_resource` sur `get_db_client()`

---

## 🏗️ Restructuration UI/UX

### Navigation "Ton Espace"
- ❌ Supprimé : barre d'onglets horizontale statique (Défis, Grammaire, Missions, Prononciation, Quiz)
- ✅ Nouveau : routeur central `st.segmented_control` avec 6 pages (Accueil, Défis, Grammaire, Missions, Prononciation, Quiz)
- ✅ Scroll automatique vers le haut à chaque changement de page

### Dashboard
- ❌ Supprimé : carte "Profil privé / Niveau verrouillé" de l'en-tête
- ❌ Masqué : les 4 métriques (Progression, Points, Activités, Objectif) par défaut
- ✅ Nouveau : bouton "📊 Dashboard" qui affiche les métriques dans un `st.expander`

---

## 📦 Dépendances supplémentaires

```bash
pip install audio-recorder-streamlit extra-streamlit-components
```

---

## 🔧 Configuration requise (secrets.toml)

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJ..."
SUPABASE_SERVICE_ROLE_KEY = "eyJ..."
GEMINI_API_KEY = "AI..."
SESSION_ENCRYPTION_KEY = "your-fernet-key-base64"
```

---

## 🚀 Lancement

```bash
streamlit run frantsay_v4_refactored.py
```
