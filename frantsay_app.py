# -*- coding: utf-8 -*-
"""
FRANTSAY — Plateforme d'apprentissage du français pour les élèves et étudiants à Madagascar.
Design : Vercel Style, Clair/Sombre, Optimisé Mobile — Sans emoji, iconographie texte minimaliste.
"""

import base64
import io
import json
import random
import hashlib
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
MODEL_NAME = "gemini-2.5-flash"
LEVELS = ["Collège", "Lycée", "Université"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le français",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# 1bis. ILLUSTRATION ROBOT — mascotte du hero, encodée en base64
# =============================================================================
# Intégrée directement dans le fichier (pas d'URL externe) pour garantir un
# affichage fiable, quel que soit l'hébergeur, sans dépendance à un CDN tiers.

ROBOT_ILLUSTRATION_B64 = "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"
ROBOT_ILLUSTRATION = "data:image/jpeg;base64," + ROBOT_ILLUSTRATION_B64

# Le thème doit être connu AVANT de construire le CSS. Le sélecteur visuel
# (st.radio) est rendu plus bas, tout en haut de la sidebar ; ici on ne fait
# que garantir que la clé existe pour ce rerun.
if "theme" not in st.session_state:
    st.session_state.theme = "light"


# =============================================================================
# 2. DESIGN — PALETTES CLAIR / SOMBRE (CSS piloté par st.session_state["theme"])
# =============================================================================

LIGHT_THEME = {
    "bg": "#FAFAFA", "card": "#FFFFFF", "ink": "#0F172A", "muted": "#64748B", "line": "#E2E8F0",
    "purple": "#4F46E5", "violet": "#7C3AED", "green": "#10B981", "amber": "#F59E0B", "red": "#EF4444",
    "soft_purple_bg": "#EEF2FF", "soft_purple_border": "#DDD6FE",
    "soft_green_bg": "#ECFDF5", "soft_green_border": "#A7F3D0", "soft_green_text": "#047857",
    "soft_amber_bg": "#FFF7ED", "soft_amber_border": "#FED7AA", "soft_amber_text": "#C2410C",
    "soft_red_bg": "#FEF2F2", "soft_red_border": "#FECACA", "soft_red_text": "#B91C1C",
    "tabs_bg": "#F1F5F9", "shadow_rgb": "15,23,42", "hero_end": "#F5F3FF",
    "footer_bg": "rgba(255,255,255,.92)", "scheme": "light",
}
DARK_THEME = {
    "bg": "#0F172A", "card": "#1E293B", "ink": "#F8FAFC", "muted": "#94A3B8", "line": "#334155",
    "purple": "#818CF8", "violet": "#A78BFA", "green": "#34D399", "amber": "#FBBF24", "red": "#F87171",
    "soft_purple_bg": "#26314F", "soft_purple_border": "#3B4A73",
    "soft_green_bg": "#123329", "soft_green_border": "#1F5C46", "soft_green_text": "#6EE7B7",
    "soft_amber_bg": "#3A2A12", "soft_amber_border": "#6B4A1E", "soft_amber_text": "#FBBF24",
    "soft_red_bg": "#3A1620", "soft_red_border": "#6B2331", "soft_red_text": "#FCA5A5",
    "tabs_bg": "#1B2436", "shadow_rgb": "0,0,0", "hero_end": "#1B2340",
    "footer_bg": "rgba(30,41,59,.92)", "scheme": "dark",
}
theme = DARK_THEME if st.session_state.theme == "dark" else LIGHT_THEME

ROOT_VARS = f"""
:root {{
    --bg: {theme['bg']};
    --card: {theme['card']};
    --ink: {theme['ink']};
    --muted: {theme['muted']};
    --line: {theme['line']};
    --purple: {theme['purple']};
    --violet: {theme['violet']};
    --green: {theme['green']};
    --amber: {theme['amber']};
    --red: {theme['red']};
    --soft-purple-bg: {theme['soft_purple_bg']};
    --soft-purple-border: {theme['soft_purple_border']};
    --soft-green-bg: {theme['soft_green_bg']};
    --soft-green-border: {theme['soft_green_border']};
    --soft-green-text: {theme['soft_green_text']};
    --soft-amber-bg: {theme['soft_amber_bg']};
    --soft-amber-border: {theme['soft_amber_border']};
    --soft-amber-text: {theme['soft_amber_text']};
    --soft-red-bg: {theme['soft_red_bg']};
    --soft-red-border: {theme['soft_red_border']};
    --soft-red-text: {theme['soft_red_text']};
    --tabs-bg: {theme['tabs_bg']};
    --shadow-rgb: {theme['shadow_rgb']};
    --hero-end: {theme['hero_end']};
    --footer-bg: {theme['footer_bg']};
    --radius: 16px;
    --footer-h: 46px;
    color-scheme: {theme['scheme']};
}}
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600&display=swap');
""" + ROOT_VARS + """

html, body, [class*="css"] {
    font-family: "Plus Jakarta Sans", "Inter", sans-serif;
}

.stApp { background: var(--bg); color: var(--ink); transition: background-color .2s ease, color .2s ease; }
h1, h2, h3, h4, h5, p, span, label, div { color: var(--ink); }

.block-container {
    max-width: 700px;
    padding-top: 1.3rem;
    padding-bottom: calc(var(--footer-h) + 1.4rem);
    padding-left: .9rem;
    padding-right: .9rem;
}

/* Cartes Vercel : bord fin, radius 16px, transition douce au changement de thème */
.card, .lesson, .tip, .mini, .st-key-hero_box {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: 0 4px 14px -6px rgba(var(--shadow-rgb), 0.06);
    transition: transform .15s cubic-bezier(.16,1,.3,1), box-shadow .15s ease,
                background-color .2s ease, border-color .2s ease;
}

.card:hover, .lesson:hover { transform: translateY(-1px); box-shadow: 0 10px 22px -10px rgba(var(--shadow-rgb),.10); }

.st-key-hero_box {
    padding: 1rem 1.1rem;
    margin-bottom: .7rem;
    background: linear-gradient(135deg, var(--card) 0%, var(--hero-end) 100%);
}
.st-key-hero_box [data-testid="stVerticalBlockBorderWrapper"] { background: transparent; border: 0; }

.hero-title {
    font-size: clamp(1.1rem, 4.2vw, 1.5rem);
    font-weight: 800;
    letter-spacing: -.5px;
    margin: .3rem 0 .2rem 0;
    line-height: 1.15;
}
.hero-sub { margin: 0; font-size: .8rem; color: var(--muted); }
.hero-robot-img { width: 100%; max-width: 78px; display: block; margin: 0 auto; filter: drop-shadow(0 4px 10px rgba(var(--shadow-rgb), .18)); }

.card { padding: .85rem .95rem; margin-bottom: .6rem; }
.mini { padding: .65rem .75rem; }

.eyebrow {
    color: var(--purple);
    font-size: .66rem;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: .35rem;
}

/* Tag minimaliste texte façon "[MG]" / "[01]" — remplace les emojis */
.tag {
    display: inline-flex; align-items: center; justify-content: center;
    font-family: "JetBrains Mono", monospace;
    font-size: .62rem; font-weight: 700; letter-spacing: .3px;
    padding: .12rem .38rem;
    border-radius: 6px;
    background: var(--soft-purple-bg);
    color: var(--purple);
    border: 1px solid var(--soft-purple-border);
}
.tag-solid { background: var(--purple); color: #fff; border-color: var(--purple); }
.tag-green { background: var(--soft-green-bg); color: var(--soft-green-text); border-color: var(--soft-green-border); }
.tag-red { background: var(--soft-red-bg); color: var(--soft-red-text); border-color: var(--soft-red-border); }

.badge {
    display: inline-flex; align-items: center; gap: .4rem;
    padding: .3rem .65rem; border-radius: 999px;
    font-size: .68rem; font-weight: 700;
}
.badge-ok { background: var(--soft-green-bg); color: var(--soft-green-text); border: 1px solid var(--soft-green-border); }
.badge-warn { background: var(--soft-amber-bg); color: var(--soft-amber-text); border: 1px solid var(--soft-amber-border); }

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

.tip { background: var(--soft-purple-bg); border-color: var(--soft-purple-border); padding: .7rem .8rem; font-size: .8rem; }

.capsule {
    display: inline-flex; flex-direction: column;
    border-radius: 12px; padding: .4rem .6rem; margin: .15rem .25rem .15rem 0;
    border: 1px solid; min-width: 90px;
}
.capsule-type { font-size: .55rem; font-weight: 800; text-transform: uppercase; letter-spacing: .4px; }
.capsule-text { font-weight: 700; margin-top: .1rem; font-size: .82rem; }

.sujet { background: var(--soft-purple-bg); border-color: var(--soft-purple-border); color: var(--purple); }
.verbe { background: var(--soft-green-bg); border-color: var(--soft-green-border); color: var(--soft-green-text); }
.complement { background: var(--soft-amber-bg); border-color: var(--soft-amber-border); color: var(--soft-amber-text); }
.autre { background: var(--tabs-bg); border-color: var(--line); color: var(--muted); }

/* Phrase modèle — carte immersive */
.phrase-modele {
    background: linear-gradient(135deg, var(--purple) 0%, var(--violet) 100%);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    color: white;
    margin-bottom: .6rem;
    box-shadow: 0 10px 24px -10px rgba(79,70,229,.5);
}
.phrase-modele .eyebrow2 {
    font-size: .62rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
    color: rgba(255,255,255,.82); margin-bottom: .3rem; display:block;
}
.phrase-modele h3 { color: white !important; margin: 0; font-size: 1.05rem; line-height: 1.35; }

/* Fautes de prononciation */
.faute {
    border: 1px solid var(--soft-amber-border); background: var(--soft-amber-bg); border-radius: 12px;
    padding: .55rem .7rem; margin-bottom: .4rem; font-size: .8rem;
}
.faute .mot { font-weight: 800; color: var(--soft-amber-text); }

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
    background: var(--card) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
}

.stTabs [data-baseweb="tab-list"] {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: .3rem;
    background: var(--tabs-bg);
    padding: .3rem;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    justify-content: center;
    border-radius: 10px;
    padding: .4rem .3rem;
    font-weight: 700;
    font-size: .66rem;
    color: var(--muted);
}
.stTabs [aria-selected="true"] { background: var(--purple) !important; color: white !important; }

/* Icônes minimalistes des onglets — st.tabs n'accepte que du texte brut dans son
   libellé (pas de HTML), donc l'icône est injectée en CSS pur via ::before,
   positionnée par index d'onglet plutôt que par contenu texte. */
.stTabs [data-baseweb="tab-list"] button p {
    display: inline-flex;
    align-items: center;
    gap: .3rem;
}
.stTabs [data-baseweb="tab-list"] button p::before {
    flex: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px; height: 16px;
    border-radius: 5px;
    background: var(--card);
    color: var(--purple);
    font-family: "JetBrains Mono", monospace;
    font-size: .52rem;
    font-weight: 800;
    border: 1px solid var(--line);
}
.stTabs [data-baseweb="tab-list"] button:nth-of-type(1) p::before { content: "•"; background: transparent; border-color: transparent; color: var(--purple); font-size: .9rem; }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(2) p::before { content: "01"; }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(3) p::before { content: "02"; }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(4) p::before { content: "03"; }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(5) p::before { content: "04"; }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"] p::before { background: rgba(255,255,255,.9); color: var(--purple); border-color: transparent; }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(1) p::before { color: #fff; }

section[data-testid="stSidebar"] { background: var(--card); border-right: 1px solid var(--line); }

/* Sélecteur de thème — sélecteur horizontal en haut de sidebar */
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex; gap: .35rem; background: var(--tabs-bg); padding: .3rem; border-radius: 12px;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    flex: 1; margin: 0 !important; padding: .3rem .4rem !important; border-radius: 9px;
    font-size: .74rem; font-weight: 700; justify-content: center;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
    background: var(--purple); color: #fff;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p { color: #fff !important; }

/* Canaux cachés JS -> Streamlit (audio du Module 03) */
.st-key-audio_bridge_slot { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }

/* Footer fixe, toujours visible quel que soit l'onglet ouvert */
.app-footer {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    height: var(--footer-h);
    display: flex; align-items: center; justify-content: center;
    background: var(--footer-bg);
    backdrop-filter: blur(6px);
    border-top: 1px solid var(--line);
    color: var(--muted);
    font-size: .72rem;
    z-index: 999;
}
.app-footer b { color: var(--ink); font-weight: 700; }

@media (max-width: 480px) {
    .stTabs [data-baseweb="tab-list"] { grid-template-columns: repeat(5, 1fr); }
    .stTabs [data-baseweb="tab"] p { font-size: .58rem !important; }
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
    "score": 0,
    "questions_done": 0,
    "last_correction": None,
    "last_dialogue": None,
    "quiz_question": None,
    "quiz_answer": None,
    "model_sentence": None,
    "pronunciation_result": None,
    "last_audio_hash": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

if st.session_state.model_sentence is None:
    st.session_state.model_sentence = random.choice(MODEL_SENTENCES[st.session_state.level])


# =============================================================================
# 6. APPELS API GEMINI — clé exclusivement lue depuis st.secrets
# =============================================================================

def get_api_key() -> str:
    """Lit GEMINI_API_KEY uniquement dans st.secrets. Aucune saisie utilisateur n'existe."""
    try:
        return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        return ""


def api_available() -> bool:
    return bool(get_api_key())


def call_gemini_structured(system_prompt: str, user_prompt: str, schema_class):
    key = get_api_key()
    if not key:
        raise ValueError("Clé API Gemini manquante côté serveur (st.secrets).")
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
        raise ValueError("Clé API Gemini manquante côté serveur (st.secrets).")
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
        raise ValueError("Clé API Gemini manquante côté serveur (st.secrets).")
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
        '<div class="tip"><span class="tag tag-red">!</span> '
        "<b>Configuration requise :</b> l'administrateur doit définir "
        "<code>GEMINI_API_KEY</code> dans les secrets de l'application. "
        "Les leçons restent consultables sans IA.</div>",
        unsafe_allow_html=True,
    )


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
# 8. ENREGISTREUR WEB AUDIO NATIF (Démarrer / Arrêter — sans coupure automatique)
# =============================================================================
# Le composant capture l'audio via MediaRecorder, le ré-encode en WAV (PCM 16 bits)
# dans le navigateur, puis transmet le résultat en base64 à Streamlit en pilotant
# directement le champ texte caché (.st-key-audio_bridge_slot), car st.components.v1.html
# n'offre pas de canal de retour natif. Dès que la valeur change côté Python,
# l'analyse Gemini démarre automatiquement — aucun fichier à téléverser.
# Les couleurs sont injectées dynamiquement (voir build_recorder_html) car cet
# iframe est un document isolé qui n'hérite pas des variables CSS de la page.

RECORDER_HTML_TEMPLATE = """
<div id="rec-wrap">
  <div class="rec-row">
    <button id="btnStart" class="rec-btn rec-start" type="button">[●] Démarrer</button>
    <button id="btnStop" class="rec-btn rec-stop" type="button" disabled>[■] Arrêter</button>
  </div>
  <div class="rec-meta">
    <span id="recDot" class="rec-dot"></span>
    <span id="recStatus" class="rec-status">Prêt à enregistrer</span>
    <span id="recTimer" class="rec-timer">00:00</span>
  </div>
</div>
<style>
  html, body { margin: 0; background: __CARD__; }
  #rec-wrap { font-family: "Plus Jakarta Sans", "Inter", sans-serif; }
  .rec-row { display: flex; gap: 8px; margin-bottom: 10px; }
  .rec-btn {
    flex: 1; border: 0; border-radius: 12px; padding: 12px 10px;
    font-weight: 700; font-size: 13px; cursor: pointer;
    transition: transform .15s ease, opacity .15s ease;
  }
  .rec-btn:active { transform: scale(0.97); }
  .rec-btn:disabled { opacity: .4; cursor: not-allowed; }
  .rec-start { background: __PURPLE__; color: #fff; box-shadow: 0 4px 12px rgba(79,70,229,.28); }
  .rec-stop { background: __RED__; color: #fff; box-shadow: 0 4px 12px rgba(239,68,68,.28); }
  .rec-meta {
    display: flex; align-items: center; gap: 8px;
    font-size: 12px; color: __MUTED__; padding: 2px 2px;
  }
  .rec-dot {
    width: 8px; height: 8px; border-radius: 50%; background: __LINE__; flex: none;
  }
  .rec-dot.live { background: __RED__; box-shadow: 0 0 0 0 rgba(239,68,68,.6); animation: pulse 1.1s infinite; }
  @keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(239,68,68,.55); }
    70% { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
  }
  .rec-status { flex: 1; color: __INK__; }
  .rec-timer { font-family: "JetBrains Mono", monospace; font-weight: 700; color: __INK__; }
</style>
<script>
(function () {
  const btnStart = document.getElementById('btnStart');
  const btnStop = document.getElementById('btnStop');
  const statusEl = document.getElementById('recStatus');
  const timerEl = document.getElementById('recTimer');
  const dotEl = document.getElementById('recDot');

  let mediaStream = null;
  let mediaRecorder = null;
  let chunks = [];
  let timerHandle = null;
  let startTs = 0;

  function setStatus(text, live) {
    statusEl.textContent = text;
    dotEl.classList.toggle('live', !!live);
  }

  function fmt(totalSeconds) {
    const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
    const s = Math.floor(totalSeconds % 60).toString().padStart(2, '0');
    return m + ':' + s;
  }

  function tick() {
    const elapsed = (Date.now() - startTs) / 1000;
    timerEl.textContent = fmt(elapsed);
  }

  function writeString(view, offset, str) {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  }

  function floatTo16BitPCM(view, offset, input) {
    for (let i = 0; i < input.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, input[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
  }

  function interleave(left, right) {
    const length = left.length + right.length;
    const result = new Float32Array(length);
    let index = 0, inputIndex = 0;
    while (index < length) {
      result[index++] = left[inputIndex];
      result[index++] = right[inputIndex];
      inputIndex++;
    }
    return result;
  }

  function audioBufferToWavBlob(buffer) {
    const numChannels = buffer.numberOfChannels;
    const sampleRate = buffer.sampleRate;
    const samples = numChannels === 2
      ? interleave(buffer.getChannelData(0), buffer.getChannelData(1))
      : buffer.getChannelData(0);

    const bytesPerSample = 2;
    const blockAlign = numChannels * bytesPerSample;
    const dataSize = samples.length * bytesPerSample;
    const arrayBuffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(arrayBuffer);

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataSize, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, dataSize, true);
    floatTo16BitPCM(view, 44, samples);

    return new Blob([view], { type: 'audio/wav' });
  }

  function pushToStreamlit(dataUrl) {
    try {
      const doc = window.parent.document;
      const target = doc.querySelector('.st-key-audio_bridge_slot input');
      if (!target) {
        setStatus('Connexion au tableau de bord introuvable.', false);
        return;
      }
      const setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
      setter.call(target, dataUrl);
      target.dispatchEvent(new Event('input', { bubbles: true }));
      target.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Enter', code: 'Enter', keyCode: 13, which: 13 }));
      setStatus('Analyse envoyée — résultat ci-dessous.', false);
    } catch (err) {
      setStatus('Échec de transmission : ' + err.message, false);
    }
  }

  async function onRecordingStop() {
    try {
      setStatus('Traitement de l\\'enregistrement...', false);
      const blob = new Blob(chunks, { type: chunks[0] ? chunks[0].type : 'audio/webm' });
      const arrayBuffer = await blob.arrayBuffer();
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioCtx();
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
      const wavBlob = audioBufferToWavBlob(audioBuffer);
      const reader = new FileReader();
      reader.onloadend = function () {
        pushToStreamlit(reader.result);
        btnStart.disabled = false;
      };
      reader.readAsDataURL(wavBlob);
    } catch (err) {
      setStatus('Erreur de traitement audio : ' + err.message, false);
      btnStart.disabled = false;
    }
  }

  async function startRecording() {
    chunks = [];
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setStatus('Micro refusé ou indisponible.', false);
      return;
    }
    mediaRecorder = new MediaRecorder(mediaStream);
    mediaRecorder.ondataavailable = function (e) { if (e.data.size > 0) chunks.push(e.data); };
    mediaRecorder.onstop = onRecordingStop;
    mediaRecorder.start();
    startTs = Date.now();
    timerEl.textContent = '00:00';
    timerHandle = setInterval(tick, 250);
    setStatus('Enregistrement en cours...', true);
    btnStart.disabled = true;
    btnStop.disabled = false;
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach(function (t) { t.stop(); });
    }
    clearInterval(timerHandle);
    btnStop.disabled = true;
    setStatus('Traitement de l\\'enregistrement...', false);
  }

  btnStart.addEventListener('click', startRecording);
  btnStop.addEventListener('click', stopRecording);
})();
</script>
"""


def build_recorder_html(t: dict) -> str:
    """Injecte les couleurs du thème actif dans l'iframe isolé de l'enregistreur."""
    return (
        RECORDER_HTML_TEMPLATE
        .replace("__CARD__", t["card"])
        .replace("__PURPLE__", t["purple"])
        .replace("__RED__", t["red"])
        .replace("__MUTED__", t["muted"])
        .replace("__LINE__", t["line"])
        .replace("__INK__", t["ink"])
    )


# =============================================================================
# 9. BARRE LATÉRALE (SIDEBAR) — thème en premier, puis niveau, sans clé API
# =============================================================================

with st.sidebar:
    THEME_OPTIONS = ["Clair", "Sombre"]
    current_idx = 1 if st.session_state.theme == "dark" else 0
    picked = st.radio(
        "Thème",
        THEME_OPTIONS,
        index=current_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio",
    )
    picked_theme = "dark" if picked == THEME_OPTIONS[1] else "light"
    if picked_theme != st.session_state.theme:
        st.session_state.theme = picked_theme
        st.rerun()

    st.markdown("## FRANTSAY")
    st.caption("Apprendre le français, étape par étape.")

    st.markdown("### Mon niveau")
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

    if api_available():
        st.markdown('<span class="badge badge-ok"><span class="dot"></span> IA connectée</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-warn">IA en attente</span>', unsafe_allow_html=True)

    st.divider()

    st.markdown("### Ma progression")
    st.metric("Points", st.session_state.score)
    st.metric("Activités", st.session_state.questions_done)


# =============================================================================
# 10. EN-TÊTE — hero compact avec illustration robot IA (st.columns([2, 1]))
# =============================================================================

status = (
    '<span class="badge badge-ok"><span class="dot"></span>Assistant IA actif</span>'
    if api_available()
    else '<span class="badge badge-warn">Cours disponibles · IA non activée</span>'
)

with st.container(key="hero_box"):
    col_text, col_robot = st.columns([2, 1], vertical_alignment="center")
    with col_text:
        st.markdown(
            f"""
            <div class="eyebrow"><span class="tag tag-solid">MG</span> TONGASOA.</div>
            <h1 class="hero-title">Prêt à progresser en français ?</h1>
            <p class="hero-sub">Comprends, pratique, écoute et ose parler — niveau {safe_html(level)}.</p>
            <div style="margin-top:.5rem">{status}</div>
            """,
            unsafe_allow_html=True,
        )
    with col_robot:
        st.markdown(
            f'<img src="{ROBOT_ILLUSTRATION}" class="hero-robot-img" alt="Robot IA" />',
            unsafe_allow_html=True,
        )


# =============================================================================
# 11. ONGLETS ET MODULES
# =============================================================================

tab_home, tab_correction, tab_missions, tab_pron, tab_quiz = st.tabs(
    ["Accueil", "Grammaire", "Missions", "Prononciation", "Quiz"]
)


# --- ONGLET : ACCUEIL / PARCOURS ---
with tab_home:
    st.markdown(
        '<div class="card"><span class="eyebrow">Parcours recommandé</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Apprendre sans se perdre</h3>"
        "<p style=\"margin:0;font-size:.8rem;color:var(--muted)\">Lis une leçon, écoute les exemples, "
        "puis utilise l'IA pour pratiquer.</p></div>",
        unsafe_allow_html=True,
    )

    relevant = [x for x in LESSONS if x["niveau"] == "Tous" or x["niveau"] == level]

    cards = []
    for lesson in relevant:
        cards.append(
            '<div class="lesson">'
            f'<b>{safe_html(lesson["titre"])}</b>'
            f'<p>{safe_html(lesson["contenu"])}</p>'
            f'<span style="font-size:.72rem;color:var(--purple);font-weight:700">Ex : {safe_html(lesson["exemple"])}</span>'
            "</div>"
        )
    grid_html = '<div class="grid-2">' + "".join(cards) + "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)


# --- ONGLET 01 : CORRECTION GRAMMATICALE ---
with tab_correction:
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag">01</span>Grammaire</span>'
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

    if st.button("Analyser ma phrase", key="analyze"):
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
                st.toast("Analyse terminée !")
            except Exception as exc:
                st.error(f"Erreur d'analyse : {exc}")

    result = st.session_state.last_correction
    if result:
        st.markdown(
            '<div class="card"><span class="eyebrow"><span class="tag tag-green">OK</span>Résultat</span>'
            '<h4 style="margin:.2rem 0">' + safe_html(result.get("phrase_corrigee", "")) + "</h4></div>",
            unsafe_allow_html=True,
        )

        parts = result.get("decomposition", [])
        if parts:
            mapping = {"Sujet": "sujet", "Verbe": "verbe", "Complément": "complement"}
            html_parts = '<div class="card"><h4 style="margin:.1rem 0 .4rem 0;font-size:.9rem">Décomposition</h4>'
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

        st.markdown('<div class="card"><h4 style="margin:.1rem 0 .4rem 0;font-size:.9rem">Explication</h4>', unsafe_allow_html=True)
        st.write(result.get("explication", ""))

        errors = result.get("erreurs", [])
        if errors:
            st.markdown("**Erreurs repérées**")
            for err in errors:
                st.markdown(
                    f"- **{err.get('erreur','')}** → {err.get('correction','')}  \n"
                    f"  *Pourquoi ?* {err.get('raison','')}"
                )

        st.markdown(f"**Prononciation :** {result.get('conseil_prononciation', '')}")
        st.markdown(f"**Mini-exercice :** {result.get('mini_exercice', '')}")
        st.markdown("</div>", unsafe_allow_html=True)


# --- ONGLET 02 : MISSIONS ---
with tab_missions:
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag">02</span>Missions</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Parler dans la vraie vie</h3></div>",
        unsafe_allow_html=True,
    )

    mission_names = [x[0] for x in MISSIONS]
    selected_name = st.selectbox("Mission", mission_names)
    selected_desc = dict(MISSIONS)[selected_name]

    st.markdown(f'<div class="tip"><b>Situation :</b> {safe_html(selected_desc)}</div>', unsafe_allow_html=True)

    if not api_available():
        show_api_notice()

    if st.button("Générer mon dialogue", key="dialogue"):
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


# --- ONGLET 03 : PRONONCIATION INTERACTIVE ---
with tab_pron:
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag">03</span>Prononciation interactive</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Entraîne ta prononciation</h3></div>",
        unsafe_allow_html=True,
    )

    # --- Phrase modèle + TTS ---
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("[↻] Nouvelle phrase", key="new_sentence"):
            st.session_state.model_sentence = random.choice(MODEL_SENTENCES[level])
            st.session_state.pronunciation_result = None
    with colB:
        listen_model = st.button("[▶] Écouter le modèle", key="listen_model")

    st.markdown(
        '<div class="phrase-modele">'
        '<span class="eyebrow2">Phrase à lire à voix haute</span>'
        f"<h3>« {safe_html(st.session_state.model_sentence)} »</h3>"
        "</div>",
        unsafe_allow_html=True,
    )

    if listen_model:
        try:
            st.audio(make_audio(st.session_state.model_sentence), format="audio/mp3")
        except Exception as exc:
            st.error(f"Audio indisponible : {exc}")

    # --- Enregistreur natif : Démarrer / Arrêter manuels ---
    st.markdown(
        '<div class="card"><span class="eyebrow">À toi de parler</span>'
        '<h4 style="margin:.2rem 0;font-size:.95rem">Enregistre-toi</h4>'
        '<p style="margin:0;font-size:.76rem;color:var(--muted)">'
        "Appuie sur « Démarrer », lis la phrase à voix haute, puis appuie sur « Arrêter ». "
        "L'analyse démarre automatiquement, sans rien télécharger.</p></div>",
        unsafe_allow_html=True,
    )

    # Canal caché : reçoit le WAV encodé en base64 envoyé par le composant JS ci-dessous.
    with st.container(key="audio_bridge_slot"):
        audio_data_url = st.text_input(
            "audio_channel",
            key="audio_channel_value",
            label_visibility="collapsed",
        )

    components.html(build_recorder_html(theme), height=110, scrolling=False)

    if audio_data_url:
        try:
            header, b64data = audio_data_url.split(",", 1)
            mime_type = header.split(";")[0].replace("data:", "") or "audio/wav"
            audio_bytes = base64.b64decode(b64data)
        except Exception:
            audio_bytes, mime_type = None, "audio/wav"

        if audio_bytes:
            audio_hash = hashlib.md5(audio_bytes).hexdigest()
            if audio_hash != st.session_state.last_audio_hash:
                if not api_available():
                    show_api_notice()
                else:
                    try:
                        with st.spinner("Analyse automatique de ta prononciation..."):
                            pronunciation_result = call_gemini_audio_structured(
                                PRONUNCIATION_PROMPT,
                                audio_bytes,
                                mime_type,
                                f"Phrase modèle attendue : {st.session_state.model_sentence}",
                                ReponsePrononciation,
                            )
                        st.session_state.pronunciation_result = pronunciation_result
                        st.session_state.last_audio_hash = audio_hash
                        st.session_state.questions_done += 1
                        st.session_state.score += max(0, int(pronunciation_result.get("score", 0)) // 10)
                        if pronunciation_result.get("score", 0) >= 80:
                            st.balloons()
                    except Exception as exc:
                        st.error(f"Erreur lors de l'analyse vocale : {exc}")
            st.audio(audio_bytes, format="audio/wav")

    pronunciation_result = st.session_state.pronunciation_result
    if pronunciation_result:
        st.markdown('<div class="card"><h4 style="margin:.1rem 0 .5rem 0;font-size:.95rem">Résultat</h4>', unsafe_allow_html=True)
        st.metric("Score de prononciation", f"{pronunciation_result.get('score', 0)}/100")

        for point in pronunciation_result.get("points_forts", []):
            st.markdown(f'<span class="tag tag-green">OK</span> {safe_html(point)}', unsafe_allow_html=True)

        fautes = pronunciation_result.get("fautes", [])
        if fautes:
            st.markdown("**Fautes précises détectées**")
            for f in fautes:
                st.markdown(
                    '<div class="faute">'
                    f'<span class="mot">{safe_html(f.get("mot",""))}</span> — '
                    f'entendu : « {safe_html(f.get("entendu",""))} », attendu : « {safe_html(f.get("attendu",""))} »<br>'
                    f'<span class="tag">i</span> {safe_html(f.get("conseil",""))}'
                    "</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.success("Aucune faute détectée — bravo !")

        st.markdown(f"**Conseil général :** {pronunciation_result.get('conseil', '')}")
        st.markdown("</div>", unsafe_allow_html=True)


# --- ONGLET 04 : QUIZ ---
with tab_quiz:
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag">04</span>Révision</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Quiz intelligent</h3></div>",
        unsafe_allow_html=True,
    )

    if st.session_state.quiz_question is None:
        if api_available():
            if st.button("Générer une question", key="new_quiz"):
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
                    st.success("Bonne réponse !")
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
# 12. FOOTER — fixe en bas, visible sur tous les modules
# =============================================================================

st.markdown(
    '<div class="app-footer"><b>FRANTSAY</b>&nbsp;·&nbsp;Conçu par RAKOTONIRINA Avosoa</div>',
    unsafe_allow_html=True,
)
