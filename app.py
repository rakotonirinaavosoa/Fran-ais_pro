# -*- coding: utf-8 -*-
"""
FRANTSAY — Plateforme d'apprentissage du français pour les élèves et étudiants à Madagascar.
Design : Light Mode "Vercel" — Optimisé Mobile
"""

import io
import json
import os
import random
import html
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

APP_NAME = "FRANTSAY"
MODEL_NAME = "gemini-3.6-flash"
LEVELS = ["Collège", "Lycée", "Université"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le français",
    page_icon="🇲🇬",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# 2. DESIGN — VERCEL STYLE, COMPACT MOBILE (CSS)
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg: #FAFAFA;
    --card: #FFFFFF;
    --ink: #0F172A;
    --muted: #64748B;
    --line: #E2E8F0;
    --purple: #4F46E5;
    --purple-soft: #EEF2FF;
    --green: #10B981;
    --radius: 16px;
}

html, body, [class*="css"] {
    font-family: "Plus Jakarta Sans", "Inter", sans-serif;
}

.stApp { background: var(--bg); color: var(--ink); }
h1, h2, h3, h4, h5, p, span, label, div { color: var(--ink); }

.block-container {
    max-width: 700px;
    padding-top: .8rem;
    padding-bottom: 1.6rem;
    padding-left: .9rem;
    padding-right: .9rem;
}

/* Cartes Vercel : blanc, bord fin, radius 16px */
.hero, .card, .lesson, .tip, .mini {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: 0 4px 14px -6px rgba(15, 23, 42, 0.06);
    transition: transform .15s cubic-bezier(.16,1,.3,1), box-shadow .15s ease;
}

.card:hover, .lesson:hover { transform: translateY(-1px); box-shadow: 0 10px 22px -10px rgba(15,23,42,.10); }

.hero {
    padding: 1rem 1.1rem;
    margin-bottom: .7rem;
    background: linear-gradient(135deg, #FFFFFF 0%, #F5F3FF 100%);
}

.hero h1 {
    font-size: clamp(1.15rem, 4.4vw, 1.55rem);
    font-weight: 800;
    letter-spacing: -.5px;
    margin: .15rem 0 .2rem 0;
    line-height: 1.15;
}

.hero p { margin: 0; font-size: .82rem; color: var(--muted); }

.card { padding: .85rem .95rem; margin-bottom: .6rem; }
.mini { padding: .65rem .75rem; }

.eyebrow {
    color: var(--purple);
    font-size: .66rem;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.badge {
    display: inline-flex; align-items: center; gap: .4rem;
    padding: .3rem .65rem; border-radius: 999px;
    font-size: .68rem; font-weight: 700;
}
.badge-ok { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
.badge-warn { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }

.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); }

/* Grille compacte 2 colonnes — coeur de l'optimisation mobile */
.grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: .5rem;
    margin-bottom: .6rem;
}

.lesson { padding: .7rem .75rem; }
.lesson b { font-size: .82rem; }
.lesson p { font-size: .76rem; margin: .25rem 0; color: var(--muted); }

.tip { background: var(--purple-soft); border-color: #DDD6FE; padding: .7rem .8rem; font-size: .8rem; }

.capsule {
    display: inline-flex; flex-direction: column;
    border-radius: 12px; padding: .4rem .6rem; margin: .15rem .25rem .15rem 0;
    border: 1px solid; min-width: 90px;
}
.capsule-type { font-size: .55rem; font-weight: 800; text-transform: uppercase; letter-spacing: .4px; }
.capsule-text { font-weight: 700; margin-top: .1rem; font-size: .82rem; }

.sujet { background: #EEF2FF; border-color: #C7D2FE; color: #4338CA; }
.verbe { background: #ECFDF5; border-color: #A7F3D0; color: #047857; }
.complement { background: #FFF7ED; border-color: #FED7AA; color: #C2410C; }
.autre { background: #F8FAFC; border-color: #E2E8F0; color: #475569; }

/* Phrase modèle — carte immersive */
.phrase-modele {
    background: linear-gradient(135deg, var(--purple) 0%, #7C3AED 100%);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    color: white;
    margin-bottom: .6rem;
    box-shadow: 0 10px 24px -10px rgba(79,70,229,.5);
}
.phrase-modele .eyebrow2 {
    font-size: .62rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
    color: #E0E7FF; margin-bottom: .3rem; display:block;
}
.phrase-modele h3 { color: white !important; margin: 0; font-size: 1.05rem; line-height: 1.35; }

/* Fautes de prononciation */
.faute {
    border: 1px solid #FED7AA; background: #FFF7ED; border-radius: 12px;
    padding: .55rem .7rem; margin-bottom: .4rem; font-size: .8rem;
}
.faute .mot { font-weight: 800; color: #C2410C; }

div.stButton > button {
    border: 0 !important;
    border-radius: 12px !important;
    padding: .55rem 1.1rem !important;
    font-weight: 700 !important;
    font-size: .85rem !important;
    background: var(--purple) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.28) !important;
    transition: transform .15s ease, box-shadow .15s ease !important;
    width: 100%;
}
div.stButton > button:hover { transform: scale(1.015); box-shadow: 0 6px 16px rgba(79, 70, 229, 0.38) !important; }
div.stButton > button:active { transform: scale(0.97); }

.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stFileUploader section {
    background: #FFFFFF !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
}

.stTabs [data-baseweb="tab-list"] {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: .3rem;
    background: #F1F5F9;
    padding: .3rem;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    justify-content: center;
    border-radius: 10px;
    padding: .4rem .3rem;
    font-weight: 700;
    font-size: .68rem;
    color: var(--muted);
}
.stTabs [aria-selected="true"] { background: var(--purple) !important; color: white !important; }

section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid var(--line); }

.footer { text-align: center; color: #94A3B8; padding: 1.2rem 0 .6rem; font-size: .72rem; }

@media (max-width: 480px) {
    .stTabs [data-baseweb="tab-list"] { grid-template-columns: repeat(5, 1fr); }
    .stTabs [data-baseweb="tab"] p { font-size: .6rem !important; }
    .grid-2 { gap: .4rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# 3. SCHÉMAS STRUCTURÉS PYDANTIC
# =============================================================================

class ErreurDetail(BaseModel):
    erreur: str = Field(description="Erreur dans la phrase")
    correction: str = Field(description="Correction proposée")
    raison: str = Field(description="Règle ou raison")


class PartDecomposition(BaseModel):
    type: str = Field(description="Sujet, Verbe ou Complément")
    texte: str = Field(description="Texte correspondant")


class ReponseCorrection(BaseModel):
    phrase_corrigee: str
    decomposition: list[PartDecomposition]
    erreurs: list[ErreurDetail]
    explication: str
    conseil_prononciation: str
    mini_exercice: str


class ReponseQuiz(BaseModel):
    question: str
    options: list[str]
    bonne_reponse: int
    explication: str


class FautePrononciation(BaseModel):
    mot: str = Field(description="Mot ou syllabe mal prononcé")
    entendu: str = Field(description="Approximation phonétique de ce qui a été entendu")
    attendu: str = Field(description="Prononciation correcte attendue")
    conseil: str = Field(description="Conseil précis et actionnable pour corriger")


class ReponsePrononciation(BaseModel):
    score: int = Field(description="Score global de 0 à 100")
    points_forts: list[str]
    fautes: list[FautePrononciation] = Field(description="Liste exacte des fautes de prononciation détectées")
    conseil: str


# =============================================================================
# 4. DONNÉES PÉDAGOGIQUES
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

MODEL_SENTENCES = {
    "Collège": [
        "Ma sœur va à l'école tous les matins.",
        "Le chat dort sous la table de la cuisine.",
        "J'aime lire des histoires avant de dormir.",
        "Nous jouons au football après les cours.",
    ],
    "Lycée": [
        "Je pense que la lecture développe l'imagination.",
        "Hier, nous avons visité le marché du village.",
        "Il faut réviser régulièrement pour réussir ses examens.",
        "Mes amis et moi préparons un exposé sur l'environnement.",
    ],
    "Université": [
        "Cette recherche démontre l'importance de la rigueur scientifique.",
        "Le débat portait sur les conséquences économiques de la décision.",
        "Il est essentiel d'analyser les sources avant de conclure.",
        "La coopération internationale reste indispensable au développement.",
    ],
}


# =============================================================================
# 5. ÉTAT DE SESSION
# =============================================================================

DEFAULT_STATE = {
    "level": "Lycée",
    "api_key": "",
    "score": 0,
    "questions_done": 0,
    "last_correction": None,
    "last_dialogue": None,
    "quiz_question": None,
    "quiz_answer": None,
    "model_sentence": None,
    "pronunciation_result": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

if st.session_state.model_sentence is None:
    st.session_state.model_sentence = random.choice(MODEL_SENTENCES[st.session_state.level])


# =============================================================================
# 6. APPELS API GEMINI STRUCTURÉS
# =============================================================================

def get_api_key() -> str:
    try:
        secret = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret = ""
    return (secret or st.session_state.api_key or os.getenv("GEMINI_API_KEY", "")).strip()


def api_available() -> bool:
    return bool(get_api_key())


def call_gemini_structured(system_prompt: str, user_prompt: str, schema_class):
    key = get_api_key()
    if not key:
        raise ValueError("Clé API Gemini manquante.")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=schema_class,
        ),
    )
    return json.loads(response.text)


def call_gemini_text(system_prompt: str, user_prompt: str) -> str:
    key = get_api_key()
    if not key:
        raise ValueError("Clé API Gemini manquante.")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config={"system_instruction": system_prompt, "temperature": 0.35},
    )
    return getattr(response, "text", "").strip()


def call_gemini_audio_structured(system_prompt: str, audio_bytes: bytes, mime_type: str, extra_text: str, schema_class):
    key = get_api_key()
    if not key:
        raise ValueError("Clé API Gemini manquante.")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            extra_text,
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.15,
            response_mime_type="application/json",
            response_schema=schema_class,
        ),
    )
    return json.loads(response.text)


def make_audio(text: str, slow: bool = False) -> io.BytesIO:
    audio = io.BytesIO()
    gTTS(text=text, lang="fr", slow=slow).write_to_fp(audio)
    audio.seek(0)
    return audio


def safe_html(text: Any) -> str:
    return html.escape(str(text))


def show_api_notice():
    st.markdown(
        '<div class="tip"><b>🔑 Active l’IA :</b> ajoute ta clé Gemini dans la barre latérale. '
        "Les leçons et la prononciation restent utilisables sans clé.</div>",
        unsafe_allow_html=True,
    )


def guess_mime(filename: str) -> str:
    ext = (filename or "").lower().rsplit(".", 1)[-1] if "." in (filename or "") else "wav"
    return {
        "wav": "audio/wav",
        "mp3": "audio/mp3",
        "ogg": "audio/ogg",
        "webm": "audio/webm",
        "m4a": "audio/mp4",
    }.get(ext, "audio/wav")


# =============================================================================
# 7. PROMPTS SYSTÈME
# =============================================================================

CORRECTION_PROMPT = """
Tu es un professeur de français spécialisé dans l'enseignement aux apprenants malgaches.
Tu dois corriger sans humilier. Explique simplement l'erreur et donne une règle mémorisable.
Prends en compte les difficultés possibles : ordre des mots influencé par le malagasy,
genre des noms, articles, conjugaison, prépositions, accords et prononciation.
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

QUIZ_PROMPT = "Crée une seule question de français adaptée au niveau indiqué."

PRONUNCIATION_PROMPT = """
Tu es un expert en phonétique française qui évalue des apprenants malgaches.
On te donne un enregistrement audio et la phrase modèle que l'apprenant devait lire à voix haute.
Compare précisément ce qui a été prononcé à la phrase attendue.
Liste UNIQUEMENT les fautes réelles et exactes que tu entends (mot par mot ou syllabe par syllabe),
avec ce qui a été entendu, ce qui était attendu, et un conseil concret pour corriger.
Ne liste pas de fautes si la prononciation est correcte. Le score est de 0 à 100.
"""


# =============================================================================
# 8. BARRE LATÉRALE (SIDEBAR)
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
    if level != st.session_state.level:
        st.session_state.level = level
        st.session_state.model_sentence = random.choice(MODEL_SENTENCES[level])
    st.session_state.level = level

    st.divider()

    st.markdown("### 🔑 Connexion IA")
    manual_key = st.text_input(
        "Clé Gemini",
        type="password",
        value=st.session_state.api_key,
        placeholder="AIza...",
        help="Définis GEMINI_API_KEY dans les secrets Streamlit.",
    )
    st.session_state.api_key = manual_key

    if api_available():
        st.markdown('<span class="badge badge-ok"><span class="dot"></span> IA connectée</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-warn">IA en attente</span>', unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📈 Ma progression")
    st.metric("Points", st.session_state.score)
    st.metric("Activités", st.session_state.questions_done)


# =============================================================================
# 9. EN-TÊTE (compact, sans bloc de statistiques)
# =============================================================================

status = (
    '<span class="badge badge-ok"><span class="dot"></span>Assistant IA actif</span>'
    if api_available()
    else '<span class="badge badge-warn">Cours disponibles · IA non activée</span>'
)

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">🇲🇬 Français pour Madagascar</div>
        <h1>Prêt à progresser en français ?</h1>
        <p>Comprends, pratique, écoute et ose parler — niveau {safe_html(level)}.</p>
        <div style="margin-top:.5rem">{status}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# 10. ONGLETS ET MODULES
# =============================================================================

tab_home, tab_correction, tab_pron, tab_missions, tab_quiz = st.tabs(
    ["🏠 Parcours", "✍️ Correction", "🔊 Prononciation", "🗣️ Missions", "🧠 Quiz"]
)


# --- ONGLET 1 : PARCOURS ---
with tab_home:
    st.markdown(
        '<div class="card"><span class="eyebrow">Parcours recommandé</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Apprendre sans se perdre</h3>"
        "<p style=\"margin:0;font-size:.8rem;color:var(--muted)\">Lis une leçon, écoute les exemples, "
        "puis utilise l'IA pour pratiquer.</p></div>",
        unsafe_allow_html=True,
    )

    relevant = [x for x in LESSONS if x["niveau"] == "Tous" or x["niveau"] == level]

    grid_html = '<div class="grid-2">'
    for lesson in relevant:
        grid_html += f"""
        <div class="lesson">
            <b>📘 {safe_html(lesson["titre"])}</b>
            <p>{safe_html(lesson["contenu"])}</p>
            <span style="font-size:.72rem;color:var(--purple);font-weight:700">Ex : {safe_html(lesson["exemple"])}</span>
        </div>
        """
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)


# --- ONGLET 2 : CORRECTION GRAMMATICALE ---
with tab_correction:
    st.markdown(
        '<div class="card"><span class="eyebrow">Module 01 · Grammaire</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Corrige ma phrase</h3>"
        "<p style=\"margin:0;font-size:.8rem;color:var(--muted)\">Écris une phrase comme tu la dirais naturellement.</p></div>",
        unsafe_allow_html=True,
    )

    text = st.text_area(
        "Phrase",
        placeholder="Exemple : Hier, je suis allé au marché avec mes amis.",
        height=100,
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
                with st.spinner("Analyse en cours..."):
                    result = call_gemini_structured(
                        CORRECTION_PROMPT,
                        f"Niveau : {level}\nPhrase de l'apprenant : {text}",
                        ReponseCorrection,
                    )
                st.session_state.last_correction = result
                st.session_state.questions_done += 1
                st.session_state.score += 5
                st.toast("Analyse terminée !", icon="✅")
            except Exception as exc:
                st.error(f"Erreur d'analyse : {exc}")

    result = st.session_state.last_correction
    if result:
        st.markdown(
            '<div class="card"><span class="eyebrow">Résultat</span>'
            '<h4 style="margin:.2rem 0">✅ ' + safe_html(result.get("phrase_corrigee", "")) + "</h4></div>",
            unsafe_allow_html=True,
        )

        parts = result.get("decomposition", [])
        if parts:
            mapping = {"Sujet": "sujet", "Verbe": "verbe", "Complément": "complement"}
            html_parts = '<div class="card"><h4 style="margin:.1rem 0 .4rem 0;font-size:.9rem">🔎 Décomposition</h4>'
            for part in parts:
                typ = str(part.get("type", "Autre"))
                cls = mapping.get(typ, "autre")
                html_parts += (
                    f'<div class="capsule {cls}">'
                    f'<span class="capsule-type">{safe_html(typ)}</span>'
                    f'<span class="capsule-text">{safe_html(part.get("texte", ""))}</span>'
                    "</div>"
                )
            html_parts += "</div>"
            st.markdown(html_parts, unsafe_allow_html=True)

        st.markdown('<div class="card"><h4 style="margin:.1rem 0 .4rem 0;font-size:.9rem">🧩 Explication</h4>', unsafe_allow_html=True)
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


# --- ONGLET 3 : PRONONCIATION INTERACTIVE ---
with tab_pron:
    # --- Phrase modèle + TTS ---
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🔁 Nouvelle phrase", key="new_sentence"):
            st.session_state.model_sentence = random.choice(MODEL_SENTENCES[level])
            st.session_state.pronunciation_result = None
    with colB:
        listen_model = st.button("🔊 Écouter le modèle", key="listen_model")

    st.markdown(
        f"""
        <div class="phrase-modele">
            <span class="eyebrow2">Phrase à lire à voix haute</span>
            <h3>« {safe_html(st.session_state.model_sentence)} »</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if listen_model:
        try:
            st.audio(make_audio(st.session_state.model_sentence), format="audio/mp3")
        except Exception as exc:
            st.error(f"Audio indisponible : {exc}")

    # --- Enregistreur natif HTML/JS ---
    st.markdown('<div class="card"><span class="eyebrow">🎙️ Enregistre-toi</span></div>', unsafe_allow_html=True)

    components.html(
        """
        <div style="font-family:'Plus Jakarta Sans',sans-serif;background:#FFFFFF;border:1px solid #E2E8F0;
                    border-radius:16px;padding:.9rem;box-sizing:border-box;">
          <div style="display:grid;grid-template-columns:repeat(2, 1fr);gap:.5rem;">
            <button id="startBtn" style="border:0;border-radius:12px;padding:.6rem;font-weight:700;
                    background:#4F46E5;color:white;font-size:.85rem;cursor:pointer;">🔴 Démarrer</button>
            <button id="stopBtn" disabled style="border:0;border-radius:12px;padding:.6rem;font-weight:700;
                    background:#94A3B8;color:white;font-size:.85rem;cursor:not-allowed;">⏹️ Arrêter</button>
          </div>
          <div id="timer" style="text-align:center;margin-top:.5rem;font-weight:700;color:#64748B;font-size:.85rem;">00:00</div>
          <audio id="player" controls style="width:100%;margin-top:.6rem;display:none;border-radius:10px;"></audio>
          <a id="downloadLink" style="display:none;margin-top:.5rem;text-align:center;background:#EEF2FF;color:#4338CA;
             border:1px solid #C7D2FE;border-radius:12px;padding:.5rem;font-weight:700;font-size:.8rem;
             text-decoration:none;">💾 Télécharger puis importe-le ci-dessous ⬇️</a>
        </div>
        <script>
        let mediaRecorder, chunks = [], startTime, timerInterval;
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const player = document.getElementById('player');
        const downloadLink = document.getElementById('downloadLink');
        const timerEl = document.getElementById('timer');

        startBtn.onclick = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                chunks = [];
                mediaRecorder.ondataavailable = e => chunks.push(e.data);
                mediaRecorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const url = URL.createObjectURL(blob);
                    player.src = url;
                    player.style.display = 'block';
                    downloadLink.href = url;
                    downloadLink.download = 'ma_prononciation.webm';
                    downloadLink.style.display = 'block';
                    clearInterval(timerInterval);
                };
                mediaRecorder.start();
                startTime = Date.now();
                timerInterval = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - startTime) / 1000);
                    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
                    const s = String(elapsed % 60).padStart(2, '0');
                    timerEl.textContent = m + ':' + s;
                }, 500);
                startBtn.disabled = true;
                startBtn.style.background = '#C7D2FE';
                startBtn.style.cursor = 'not-allowed';
                stopBtn.disabled = false;
                stopBtn.style.background = '#EF4444';
                stopBtn.style.cursor = 'pointer';
            } catch (err) {
                alert("Microphone inaccessible : " + err.message);
            }
        };

        stopBtn.onclick = () => {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
            startBtn.disabled = false;
            startBtn.style.background = '#4F46E5';
            startBtn.style.cursor = 'pointer';
            stopBtn.disabled = true;
            stopBtn.style.background = '#94A3B8';
            stopBtn.style.cursor = 'not-allowed';
        };
        </script>
        """,
        height=230,
    )

    uploaded_audio = st.file_uploader(
        "Importer mon enregistrement",
        type=["wav", "mp3", "ogg", "webm", "m4a"],
        label_visibility="collapsed",
    )

    if uploaded_audio is not None:
        audio_bytes = uploaded_audio.read()
        st.audio(audio_bytes)

        if not api_available():
            show_api_notice()
        elif st.button("✨ Analyser ma prononciation", key="analyze_pronunciation"):
            try:
                with st.spinner("Analyse détaillée en cours..."):
                    mime_type = guess_mime(uploaded_audio.name)
                    pronunciation_result = call_gemini_audio_structured(
                        PRONUNCIATION_PROMPT,
                        audio_bytes,
                        mime_type,
                        f"Phrase modèle attendue : {st.session_state.model_sentence}",
                        ReponsePrononciation,
                    )
                    st.session_state.pronunciation_result = pronunciation_result
                    st.session_state.questions_done += 1
                    st.session_state.score += max(0, int(pronunciation_result.get("score", 0)) // 10)
                if pronunciation_result.get("score", 0) >= 80:
                    st.balloons()
            except Exception as exc:
                st.error(f"Erreur lors de l'analyse vocale : {exc}")

    pronunciation_result = st.session_state.pronunciation_result
    if pronunciation_result:
        st.markdown('<div class="card"><h4 style="margin:.1rem 0 .5rem 0;font-size:.95rem">🎯 Résultat</h4>', unsafe_allow_html=True)
        st.metric("Score de prononciation", f"{pronunciation_result.get('score', 0)}/100")

        for point in pronunciation_result.get("points_forts", []):
            st.markdown(f"✅ {point}")

        fautes = pronunciation_result.get("fautes", [])
        if fautes:
            st.markdown("**Fautes précises détectées**")
            for f in fautes:
                st.markdown(
                    f"""<div class="faute">
                    <span class="mot">{safe_html(f.get('mot',''))}</span> —
                    entendu : « {safe_html(f.get('entendu',''))} », attendu : « {safe_html(f.get('attendu',''))} »<br>
                    💡 {safe_html(f.get('conseil',''))}
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.success("Aucune faute détectée — bravo !")

        st.markdown(f"**💡 Conseil général :** {pronunciation_result.get('conseil', '')}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Atelier phonétique (paires minimales) ---
    st.markdown('<div class="card"><span class="eyebrow">Module 02 · Phonétique</span><h4 style="margin:.2rem 0;font-size:.95rem">Atelier Prononciation</h4></div>', unsafe_allow_html=True)
    for idx, item in enumerate(PRONUNCIATION):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**{item['titre']}**")
        st.caption(item["explication"])

        cols = st.columns(len(item["paires"]))
        for j, (a, b) in enumerate(item["paires"]):
            with cols[j]:
                st.markdown(f"**{a}** ↔ **{b}**")
                if st.button("🔊", key=f"listen_{idx}_{j}"):
                    try:
                        st.audio(make_audio(a, slow=True), format="audio/mp3")
                        st.audio(make_audio(b, slow=True), format="audio/mp3")
                    except Exception as exc:
                        st.error(f"Audio indisponible : {exc}")
        st.markdown("</div>", unsafe_allow_html=True)


# --- ONGLET 4 : MISSIONS ---
with tab_missions:
    st.markdown(
        '<div class="card"><span class="eyebrow">Module 03 · Communication</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Parler dans la vraie vie</h3></div>",
        unsafe_allow_html=True,
    )

    mission_names = [x[0] for x in MISSIONS]
    selected_name = st.selectbox("Mission", mission_names)
    selected_desc = dict(MISSIONS)[selected_name]

    st.markdown(f'<div class="tip"><b>Situation :</b> {safe_html(selected_desc)}</div>', unsafe_allow_html=True)

    if not api_available():
        show_api_notice()

    if st.button("🗣️ Générer mon dialogue", key="dialogue"):
        if not api_available():
            show_api_notice()
        else:
            try:
                with st.spinner("Création de la situation..."):
                    dialogue = call_gemini_text(
                        DIALOGUE_PROMPT,
                        f"Niveau : {level}\nMission : {selected_name}\nObjectif : {selected_desc}",
                    )
                st.session_state.last_dialogue = dialogue
                st.session_state.questions_done += 1
                st.session_state.score += 10
            except Exception as exc:
                st.error(f"Erreur : {exc}")

    if st.session_state.last_dialogue:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(st.session_state.last_dialogue)
        st.markdown("</div>", unsafe_allow_html=True)


# --- ONGLET 5 : QUIZ ---
with tab_quiz:
    st.markdown(
        '<div class="card"><span class="eyebrow">Module 04 · Révision</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Quiz intelligent</h3></div>",
        unsafe_allow_html=True,
    )

    if st.session_state.quiz_question is None:
        if api_available():
            if st.button("🧠 Générer une question", key="new_quiz"):
                try:
                    with st.spinner("Préparation..."):
                        q_data = call_gemini_structured(
                            QUIZ_PROMPT,
                            f"Niveau : {level}. Question sur grammaire, vocabulaire ou conjugaison.",
                            ReponseQuiz,
                        )
                        st.session_state.quiz_question = q_data
                        st.rerun()
                except Exception as exc:
                    st.error(f"Erreur du quiz : {exc}")
        else:
            show_api_notice()
    else:
        q = st.session_state.quiz_question
        st.markdown(f"**{q.get('question', '')}**")
        options = q.get("options", [])

        answer = st.radio("Choisis une réponse", options, index=None, key="quiz_answer", label_visibility="collapsed")

        if st.button("Valider", key="validate_quiz"):
            if answer is None:
                st.warning("Choisis une réponse.")
            else:
                correct_index = int(q.get("bonne_reponse", 0))
                correct = options[correct_index] if options and correct_index < len(options) else ""
                if answer == correct:
                    st.success("🎉 Bonne réponse !")
                    st.session_state.score += 10
                    st.balloons()
                else:
                    st.error(f"Pas tout à fait. La bonne réponse était : {correct}")
                st.info(q.get("explication", ""))
                st.session_state.questions_done += 1

        if st.button("Nouvelle question", key="reset_quiz"):
            st.session_state.quiz_question = None
            st.session_state.quiz_answer = None
            st.rerun()


# =============================================================================
# 11. FOOTER
# =============================================================================

st.markdown(
    '<div class="footer">FRANTSAY 🇲🇬 · Apprendre le français avec confiance · '
    "Conçu par RAKOTONIRINA Avosoa</div>",
    unsafe_allow_html=True,
)
