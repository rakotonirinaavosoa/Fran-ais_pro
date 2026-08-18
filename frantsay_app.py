# -*- coding: utf-8 -*-
"""
FRANTSAY — Plateforme d'apprentissage du français pour les élèves et étudiants à Madagascar.

Version améliorée :
- Interface moderne et responsive
- Parcours par niveau
- Correction pédagogique avec Gemini
- Prononciation avec gTTS
- Missions/dialogues contextualisés à Madagascar
- Mini-leçons, quiz et progression locale
- Gestion robuste des erreurs API
- Compatible Streamlit + google-genai
"""

import io
import json
import os
import re
import html
import random
from typing import Any, Dict, List

import streamlit as st


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

APP_NAME = "FRANTSAY"
MODEL_NAME = "gemini-2.0-flash"
LEVELS = ["Collège", "Lycée", "Université"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le français",
    page_icon="🇲🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# 2. DESIGN
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: "Plus Jakarta Sans", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(99,102,241,.13), transparent 28%),
        radial-gradient(circle at 95% 10%, rgba(16,185,129,.10), transparent 24%),
        linear-gradient(135deg,#eef2ff 0%,#f8fafc 48%,#eef2ff 100%);
    color:#0f172a;
}

h1,h2,h3,h4,h5,p,span,label,div { color:#0f172a; }

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    background:rgba(255,255,255,.82);
    border:1px solid rgba(255,255,255,.95);
    border-radius:30px;
    padding:2rem 2.4rem;
    box-shadow:0 18px 45px rgba(15,23,42,.07);
    backdrop-filter:blur(18px);
    margin-bottom:1.5rem;
}

.hero h1 {
    font-size:clamp(1.8rem,3vw,2.7rem);
    font-weight:800;
    letter-spacing:-1.2px;
    margin:0;
}

.hero p { color:#64748b; margin:.45rem 0 0; }

.card {
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:24px;
    padding:1.45rem 1.6rem;
    margin-bottom:1rem;
    box-shadow:0 10px 30px rgba(15,23,42,.045);
}

.card h3,.card h4 { margin-top:0; }

.eyebrow {
    color:#4f46e5;
    font-size:.72rem;
    font-weight:800;
    letter-spacing:.9px;
    text-transform:uppercase;
}

.badge {
    display:inline-flex;
    align-items:center;
    gap:.45rem;
    padding:.42rem .8rem;
    border-radius:999px;
    font-size:.78rem;
    font-weight:700;
}

.badge-ok { background:#ecfdf5; color:#047857; border:1px solid #a7f3d0; }
.badge-warn { background:#fff7ed; color:#c2410c; border:1px solid #fed7aa; }

.dot {
    width:8px;height:8px;border-radius:50%;background:#10b981;
    box-shadow:0 0 8px #10b981;
}

.stat {
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:20px;
    padding:1rem 1.2rem;
}

.stat-number { font-size:1.65rem;font-weight:800; }
.stat-label { color:#64748b;font-size:.8rem; }

.lesson {
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:18px;
    padding:1rem 1.1rem;
    margin:.65rem 0;
}

.tip {
    background:#eef2ff;
    border:1px solid #c7d2fe;
    border-radius:16px;
    padding:1rem;
}

.capsule {
    display:inline-flex;
    flex-direction:column;
    border-radius:16px;
    padding:.65rem .9rem;
    margin:.25rem .4rem .25rem 0;
    border:1px solid;
    min-width:125px;
}

.capsule-type {
    font-size:.62rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:.5px;
}

.capsule-text { font-weight:700; margin-top:.15rem; }

.sujet { background:#eef2ff;border-color:#c7d2fe;color:#4338ca; }
.verbe { background:#ecfdf5;border-color:#a7f3d0;color:#047857; }
.complement { background:#fff7ed;border-color:#fed7aa;color:#c2410c; }
.autre { background:#f8fafc;border-color:#e2e8f0;color:#475569; }

div.stButton > button {
    border:0;
    border-radius:15px;
    padding:.68rem 1.2rem;
    font-weight:700;
    background:linear-gradient(135deg,#4f46e5,#6366f1);
    color:white !important;
    box-shadow:0 6px 16px rgba(79,70,229,.22);
}

div.stButton > button:hover {
    transform:translateY(-1px);
    box-shadow:0 9px 22px rgba(79,70,229,.30);
}

.stTextInput input, .stTextArea textarea {
    background:#fff !important;
    color:#0f172a !important;
    border:1px solid #e2e8f0 !important;
    border-radius:15px !important;
}

section[data-testid="stSidebar"] {
    background:#fff;
    border-right:1px solid #e2e8f0;
}

.footer {
    text-align:center;
    color:#94a3b8;
    padding:2rem 0 1rem;
    font-size:.82rem;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# 3. DONNÉES PÉDAGOGIQUES
# =============================================================================

PRONUNCIATION = [
    {
        "titre": "Le son [u] et le son [ou]",
        "explication": "Dans « tu », les lèvres sont arrondies et la langue reste vers l'avant. Dans « tout », le son est plus en arrière.",
        "paires": [("tu", "tout"), ("rue", "roue"), ("dessus", "dessous")],
    },
    {
        "titre": "Le son [b] et le son [v]",
        "explication": "Pour [b], les deux lèvres se ferment. Pour [v], les dents supérieures touchent légèrement la lèvre inférieure.",
        "paires": [("bas", "vas"), ("beau", "veau"), ("bon", "vont")],
    },
    {
        "titre": "Les voyelles nasales",
        "explication": "Dans « pain », « bon » et « un », l'air passe aussi par le nez. Il ne faut pas prononcer le n ou le m comme une consonne finale.",
        "paires": [("pain", "paix"), ("bon", "beau"), ("un", "eu")],
    },
]

MISSIONS = [
    ("Au marché", "Négocier le prix d'un produit avec respect."),
    ("À l'université", "Se présenter à un enseignant ou à un nouveau camarade."),
    ("Entretien d'embauche", "Répondre à des questions simples et professionnelles."),
    ("Dans la ville", "Demander et comprendre un itinéraire."),
    ("À la bibliothèque", "Demander un livre et comprendre les consignes."),
    ("Dans un service public", "Expliquer clairement une demande administrative."),
]

LESSONS = [
    {
        "titre": "Accorder le sujet et le verbe",
        "niveau": "Tous",
        "contenu": "Le verbe s'accorde avec son sujet : « Je vais », « Nous allons », « Les étudiants travaillent ».",
        "exemple": "Les élèves révisent le français.",
    },
    {
        "titre": "Choisir « à », « au », « aux »",
        "niveau": "Lycée",
        "contenu": "On dit « à l'université », « au marché », « aux cours ». Le choix dépend du nom qui suit.",
        "exemple": "Je vais à l'université. / Je vais au marché.",
    },
    {
        "titre": "Les articles : un, une, des",
        "niveau": "Collège",
        "contenu": "« Un » accompagne un nom masculin singulier, « une » un nom féminin singulier et « des » le pluriel.",
        "exemple": "un livre, une école, des étudiants.",
    },
    {
        "titre": "Relier ses idées",
        "niveau": "Université",
        "contenu": "Utilise « parce que », « donc », « cependant », « ensuite » pour construire un discours plus clair.",
        "exemple": "Je travaille, parce que je veux réussir.",
    },
]


# =============================================================================
# 4. ÉTAT
# =============================================================================

DEFAULT_STATE = {
    "level": "Lycée",
    "api_key": "",
    "score": 0,
    "questions_done": 0,
    "last_correction": None,
    "last_dialogue": None,
    "quiz_index": 0,
    "quiz_score": 0,
    "quiz_feedback": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =============================================================================
# 5. GEMINI / OUTILS
# =============================================================================

def get_api_key() -> str:
    try:
        secret = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret = ""
    return (secret or st.session_state.api_key or os.getenv("GEMINI_API_KEY", "")).strip()


def api_available() -> bool:
    return bool(get_api_key())


def call_gemini(system_prompt: str, user_prompt: str) -> str:
    key = get_api_key()
    if not key:
        raise ValueError("Clé API Gemini manquante.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.35,
        ),
    )
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini n'a renvoyé aucun contenu.")
    return text.strip()


def extract_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if not match:
            raise ValueError("La réponse de l'IA n'est pas un JSON valide.")
        return json.loads(match.group(0))


def make_audio(text: str, slow: bool = False) -> io.BytesIO:
    from gtts import gTTS
    audio = io.BytesIO()
    gTTS(text=text, lang="fr", slow=slow).write_to_fp(audio)
    audio.seek(0)
    return audio


def safe_html(text: Any) -> str:
    return html.escape(str(text))


def show_api_notice():
    st.markdown(
        '<div class="tip"><b>🔑 Active l’IA :</b> ajoute ta clé Gemini dans la barre latérale. '
        "La partie cours, prononciation et quiz reste utilisable sans clé.</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# 6. PROMPTS
# =============================================================================

CORRECTION_PROMPT = """
Tu es un professeur de français spécialisé dans l'enseignement aux apprenants malgaches.
Tu dois corriger sans humilier. Explique simplement l'erreur et donne une règle mémorisable.
Prends en compte les difficultés possibles : ordre des mots influencé par le malagasy,
genre des noms, articles, conjugaison, prépositions, accords et prononciation.

Réponds UNIQUEMENT avec un JSON valide :
{
  "phrase_corrigee": "...",
  "decomposition": [
    {"type": "Sujet", "texte": "..."},
    {"type": "Verbe", "texte": "..."},
    {"type": "Complément", "texte": "..."}
  ],
  "erreurs": [
    {"erreur": "...", "correction": "...", "raison": "..."}
  ],
  "explication": "...",
  "conseil_prononciation": "...",
  "mini_exercice": "..."
}
"""

DIALOGUE_PROMPT = """
Tu es un professeur de français FLE et tu crées des situations utiles à Madagascar.
Génère un dialogue naturel de 8 à 10 répliques adapté au niveau demandé.
Évite le français artificiel. Ajoute quelques expressions réellement utiles.
Structure en Markdown avec exactement :
## Dialogue
## Vocabulaire à retenir
## Point de grammaire
## Défi
"""

QUIZ_PROMPT = """
Crée une seule question de français adaptée au niveau indiqué.
Réponds uniquement en JSON :
{
  "question": "...",
  "options": ["...", "...", "...", "..."],
  "bonne_reponse": 0,
  "explication": "..."
}
"""


# =============================================================================
# 7. SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## 🇲🇬 FRANTSAY")
    st.caption("Apprendre le français, étape par étape.")

    st.markdown("### 🎓 Mon niveau")
    level = st.selectbox(
        "Niveau",
        LEVELS,
        index=LEVELS.index(st.session_state.level),
        label_visibility="collapsed",
    )
    st.session_state.level = level

    st.divider()

    st.markdown("### 🔑 Connexion IA")
    manual_key = st.text_input(
        "Clé Gemini",
        type="password",
        value=st.session_state.api_key,
        placeholder="AIza...",
        help="Tu peux aussi définir GEMINI_API_KEY dans les secrets Streamlit.",
    )
    st.session_state.api_key = manual_key

    if api_available():
        st.markdown(
            '<span class="badge badge-ok"><span class="dot"></span> IA connectée</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="badge badge-warn">IA en attente</span>',
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### 📈 Ma progression")
    st.metric("Points", st.session_state.score)
    st.metric("Activités", st.session_state.questions_done)

    st.caption("Conseil : pratique 10 à 15 minutes chaque jour plutôt que tout apprendre en une fois.")


# =============================================================================
# 8. HEADER
# =============================================================================

status = (
    '<span class="badge badge-ok"><span class="dot"></span>Assistant IA actif</span>'
    if api_available()
    else '<span class="badge badge-warn">Cours disponibles · IA non activée</span>'
)

st.markdown(
    f"""
    <div class="hero">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap">
            <div>
                <div class="eyebrow">🇲🇬 Français pour Madagascar</div>
                <h1>Bonjour ! Prêt à progresser ?</h1>
                <p>Un espace simple pour comprendre, pratiquer, écouter et oser parler français — niveau {safe_html(level)}.</p>
            </div>
            <div>{status}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# 9. STATS
# =============================================================================

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="stat"><div class="stat-number">🎯</div><div class="stat-label">Objectif : communiquer</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat"><div class="stat-number">{st.session_state.score}</div><div class="stat-label">Points gagnés</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat"><div class="stat-number">{st.session_state.questions_done}</div><div class="stat-label">Activités terminées</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="stat"><div class="stat-number">🇫🇷</div><div class="stat-label">Français pratique</div></div>', unsafe_allow_html=True)

st.write("")


# =============================================================================
# 10. ONGLETS
# =============================================================================

tab_home, tab_correction, tab_pron, tab_missions, tab_quiz = st.tabs(
    ["🏠 Parcours", "✍️ Correction IA", "🔊 Prononciation", "🗣️ Missions", "🧠 Quiz"]
)


# =============================================================================
# PARCOURS
# =============================================================================

with tab_home:
    st.markdown('<div class="card"><span class="eyebrow">Parcours recommandé</span><h3>Apprendre sans se perdre</h3><p>Commence par une petite leçon, écoute les exemples, puis utilise l'IA pour pratiquer.</p></div>', unsafe_allow_html=True)

    relevant = [
        x for x in LESSONS
        if x["niveau"] == "Tous" or x["niveau"] == level
    ]

    cols = st.columns(2)
    for i, lesson in enumerate(relevant):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="lesson">
                    <b>📘 {safe_html(lesson["titre"])}</b>
                    <p>{safe_html(lesson["contenu"])}</p>
                    <b>Exemple :</b> {safe_html(lesson["exemple"])}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="tip"><b>💡 Méthode :</b> lis → écoute → répète → écris → parle. '
        "L'objectif n'est pas d'être parfait dès le début, mais de progresser régulièrement.</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# CORRECTION
# =============================================================================

with tab_correction:
    st.markdown('<div class="card"><span class="eyebrow">Module 01 · Grammaire</span><h3>Corrige ma phrase</h3><p>Écris une phrase comme tu la dirais naturellement. L'IA explique ensuite les erreurs au lieu de donner seulement la réponse.</p></div>', unsafe_allow_html=True)

    text = st.text_area(
        "Phrase",
        placeholder="Exemple : Hier, je suis allé au marché avec mes amis.",
        height=130,
        label_visibility="collapsed",
    )

    if not api_available():
        show_api_notice()

    if st.button("✨ Analyser ma phrase", key="analyze"):
        if not text.strip():
            st.warning("Écris d'abord une phrase.")
        elif not api_available():
            show_api_notice()
        else:
            try:
                with st.spinner("Je cherche les erreurs et les explique..."):
                    raw = call_gemini(
                        CORRECTION_PROMPT,
                        f"Niveau : {level}\nPhrase de l'apprenant : {text}",
                    )
                    result = extract_json(raw)

                st.session_state.last_correction = result
                st.session_state.questions_done += 1
                st.session_state.score += 5

            except Exception as exc:
                st.error(f"Impossible d'effectuer l'analyse : {exc}")

    result = st.session_state.last_correction
    if result:
        st.markdown('<div class="card"><span class="eyebrow">Résultat</span><h3>✅ Phrase corrigée</h3><h4>' + safe_html(result.get("phrase_corrigee", "")) + '</h4></div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><h4>🔎 Décomposition</h4>', unsafe_allow_html=True)
        mapping = {
            "Sujet": "sujet",
            "Verbe": "verbe",
            "Complément": "complement",
        }
        parts = result.get("decomposition", [])
        if parts:
            html_parts = ""
            for part in parts:
                typ = str(part.get("type", "Autre"))
                cls = mapping.get(typ, "autre")
                html_parts += (
                    f'<div class="capsule {cls}">'
                    f'<span class="capsule-type">{safe_html(typ)}</span>'
                    f'<span class="capsule-text">{safe_html(part.get("texte", ""))}</span>'
                    "</div>"
                )
            st.markdown(html_parts, unsafe_allow_html=True)
        else:
            st.info("La décomposition n'a pas été fournie.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><h4>🧩 Ce qu'il faut comprendre</h4>', unsafe_allow_html=True)
        st.write(result.get("explication", ""))

        errors = result.get("erreurs", [])
        if errors:
            st.markdown("**Erreurs repérées**")
            for err in errors:
                st.markdown(
                    f"- **{err.get('erreur','')}** → {err.get('correction','')}  \n"
                    f"  *Pourquoi ?* {err.get('raison','')}"
                )

        st.markdown(f"**🗣️ Prononciation :** {result.get('conseil_prononciation', '')}")
        st.markdown(f"**🎯 Mini-exercice :** {result.get('mini_exercice', '')}")
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# PRONONCIATION
# =============================================================================

with tab_pron:
    st.markdown('<div class="card"><span class="eyebrow">Module 02 · Phonétique</span><h3>Atelier Prononciation</h3><p>Écoute lentement, répète plusieurs fois, puis essaie sans regarder le texte.</p></div>', unsafe_allow_html=True)

    for idx, item in enumerate(PRONUNCIATION):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### {item['titre']}")
        st.write(item["explication"])

        cols = st.columns(len(item["paires"]))
        for j, (a, b) in enumerate(item["paires"]):
            with cols[j]:
                st.markdown(f"**{a}**  ↔  **{b}**")
                if st.button("🔊 Écouter", key=f"listen_{idx}_{j}"):
                    try:
                        st.audio(make_audio(a, slow=True), format="audio/mp3")
                        st.audio(make_audio(b, slow=True), format="audio/mp3")
                    except Exception as exc:
                        st.error(f"Audio indisponible : {exc}")
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# MISSIONS
# =============================================================================

with tab_missions:
    st.markdown('<div class="card"><span class="eyebrow">Module 03 · Communication</span><h3>Parler dans la vraie vie</h3><p>Les situations sont inspirées de la vie quotidienne d'un élève ou étudiant à Madagascar.</p></div>', unsafe_allow_html=True)

    mission_names = [x[0] for x in MISSIONS]
    selected_name = st.selectbox("Mission", mission_names)
    selected_desc = dict(MISSIONS)[selected_name]

    st.markdown(
        f'<div class="tip"><b>Situation :</b> {safe_html(selected_desc)}</div>',
        unsafe_allow_html=True,
    )

    if not api_available():
        show_api_notice()

    if st.button("🗣️ Générer mon dialogue", key="dialogue"):
        if not api_available():
            show_api_notice()
        else:
            try:
                with st.spinner("Création d'une situation réaliste..."):
                    dialogue = call_gemini(
                        DIALOGUE_PROMPT,
                        f"Niveau : {level}\nMission : {selected_name}\nObjectif : {selected_desc}",
                    )
                st.session_state.last_dialogue = dialogue
                st.session_state.questions_done += 1
                st.session_state.score += 10
            except Exception as exc:
                st.error(f"Impossible de générer le dialogue : {exc}")

    if st.session_state.last_dialogue:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(st.session_state.last_dialogue)
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# QUIZ
# =============================================================================

with tab_quiz:
    st.markdown('<div class="card"><span class="eyebrow">Module 04 · Révision</span><h3>Quiz intelligent</h3><p>Une question à la fois. Après ta réponse, tu reçois une explication.</p></div>', unsafe_allow_html=True)

    if "quiz_question" not in st.session_state:
        st.session_state.quiz_question = None

    if st.session_state.quiz_question is None:
        if api_available():
            if st.button("🧠 Générer une question", key="new_quiz"):
                try:
                    with st.spinner("Préparation de la question..."):
                        raw = call_gemini(
                            QUIZ_PROMPT,
                            f"Niveau : {level}. Crée une question sur grammaire, vocabulaire ou conjugaison.",
                        )
                        st.session_state.quiz_question = extract_json(raw)
                        st.session_state.quiz_feedback = ""
                        st.rerun()
                except Exception as exc:
                    st.error(f"Erreur du quiz : {exc}")
        else:
            show_api_notice()
            st.markdown(
                """
                <div class="lesson">
                <b>Question rapide</b><br><br>
                Complète : « Nous ___ au marché demain. »
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Voir la réponse", key="static_answer"):
                st.success("Réponse : « irons ». Le sujet « nous » appelle la forme « irons » du verbe aller au futur.")
                st.session_state.score += 5
    else:
        q = st.session_state.quiz_question
        st.markdown(f"### {q.get('question', '')}")
        options = q.get("options", [])

        answer = st.radio(
            "Choisis une réponse",
            options,
            index=None,
            key="quiz_answer",
        )

        if st.button("Valider", key="validate_quiz"):
            if answer is None:
                st.warning("Choisis une réponse.")
            else:
                correct_index = int(q.get("bonne_reponse", 0))
                correct = options[correct_index] if options and correct_index < len(options) else ""
                if answer == correct:
                    st.success("🎉 Bonne réponse !")
                    st.session_state.score += 10
                else:
                    st.error(f"Pas tout à fait. La bonne réponse était : {correct}")
                st.info(q.get("explication", ""))
                st.session_state.questions_done += 1
                st.session_state.quiz_question = None
                st.session_state.quiz_answer = None

        if st.button("Nouvelle question", key="reset_quiz"):
            st.session_state.quiz_question = None
            st.session_state.quiz_answer = None
            st.rerun()


# =============================================================================
# FOOTER
# =============================================================================

st.markdown(
    '<div class="footer">FRANTSAY 🇲🇬 · Apprendre le français avec confiance · '
    "Conçu pour les apprenants à Madagascar</div>",
    unsafe_allow_html=True,
)
