# -*- coding: utf-8 -*-
"""
FRANTSAY — Application d'apprentissage du français pour Madagascar.
Version moderne : Style Bento Grid Soft UI + Analyse vocale par micro (Gemini Multimodal).
"""

import io
import json
import os
import re
import html
from typing import Any, Dict

import streamlit as st
from audio_recorder_streamlit import audio_recorder

# =============================================================================
# 1. CONFIGURATION
# =============================================================================

APP_NAME = "FRANTSAY"
MODEL_NAME = "gemini-3.6-flash"
LEVELS = ["Collège", "Lycée", "Université"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le français",
    page_icon="🇲🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 2. DESIGN — BENTO GRID SOFT UI
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --bg-main: #FFFBF7;
    --card-bg: #FFFFFF;
    --text-primary: #1E293B;
    --text-muted: #64748B;
    --accent-purple: #6366F1;
    --accent-orange: #FF8A65;
    --card-radius: 28px;
    --border-soft: #F1F5F9;
}

html, body, [class*="css"] {
    font-family: "Plus Jakarta Sans", sans-serif;
}

.stApp {
    background-color: var(--bg-main);
    color: var(--text-primary);
}

h1, h2, h3, h4, h5, p, span, label, div { color: var(--text-primary); }

.block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, #6366F1 0%, #818CF8 100%);
    border-radius: var(--card-radius);
    padding: 2rem;
    color: white !important;
    margin-bottom: 1.5rem;
    box-shadow: 0 12px 30px rgba(99, 102, 241, 0.15);
}
.hero h1, .hero p, .hero div { color: white !important; }

/* Bento Card Style */
.bento-card {
    background: var(--card-bg);
    border-radius: var(--card-radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid var(--border-soft);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03);
}

.bento-stat {
    background: #F8FAFC;
    border-radius: 20px;
    padding: 1rem;
    text-align: center;
    border: 1px solid #E2E8F0;
}
.stat-val { font-size: 1.6rem; font-weight: 800; color: var(--accent-purple); }
.stat-lbl { font-size: 0.8rem; color: var(--text-muted); font-weight: 600; }

/* Badges */
.badge-ok { background: #ECFDF5; color: #047857; padding: 6px 14px; border-radius: 99px; font-weight: 700; font-size: 0.8rem; }
.badge-warn { background: #FFF7ED; color: #C2410C; padding: 6px 14px; border-radius: 99px; font-weight: 700; font-size: 0.8rem; }

/* Capsules Grammaticales */
.capsule {
    display: inline-block;
    border-radius: 14px;
    padding: 8px 14px;
    margin: 4px;
    font-weight: 700;
    font-size: 0.85rem;
}
.sujet { background: #EEF2FF; color: #4338CA; }
.verbe { background: #ECFDF5; color: #047857; }
.complement { background: #FFF7ED; color: #C2410C; }
.autre { background: #F8FAFC; color: #475569; }

/* Buttons */
div.stButton > button {
    border-radius: 18px;
    font-weight: 700;
    background: var(--accent-purple);
    color: white !important;
    border: none;
    padding: 0.6rem 1.2rem;
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.25);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# =============================================================================
# 3. DONNÉES PÉDAGOGIQUES (INCHANGÉES)
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
# 4. ÉTAT ET MOTEUR IA MULTIMODAL
# =============================================================================

DEFAULT_STATE = {
    "level": "Lycée",
    "api_key": "",
    "score": 0,
    "questions_done": 0,
    "last_correction": None,
    "last_dialogue": None,
}

for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

def get_api_key() -> str:
    try:
        secret = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret = ""
    return (secret or st.session_state.api_key or os.getenv("GEMINI_API_KEY", "")).strip()

def api_available() -> bool:
    return bool(get_api_key())

def call_gemini(system_prompt: str, user_prompt: str) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=get_api_key())
    res = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.35),
    )
    return res.text.strip()

def analyze_pronunciation_audio(audio_bytes: bytes, target_text: str) -> str:
    from google import genai
    client = genai.Client(api_key=get_api_key())
    prompt = f"""
    Tu es un expert en phonétique du français pour apprenants malgaches.
    Écoute cet enregistrement audio. L'élève devait prononcer la phrase ou les mots suivants : "{target_text}".
    Donne un retour pédagogique structuré en Français avec :
    1. Un score de précision sur 10.
    2. Les mots ou sons mal prononcés (surtout les confusions courantes [u]/[ou], [b]/[v], ou nasales).
    3. Un conseil clair pour ajuster la position des lèvres ou de la langue.
    """
    res = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            prompt,
            {"mime_type": "audio/wav", "data": audio_bytes}
        ]
    )
    return res.text

def make_audio(text: str, slow: bool = False) -> io.BytesIO:
    from gtts import gTTS
    audio = io.BytesIO()
    gTTS(text=text, lang="fr", slow=slow).write_to_fp(audio)
    audio.seek(0)
    return audio

# =============================================================================
# 5. INTERFACE UTILISATEUR
# =============================================================================

with st.sidebar:
    st.title("🇲🇬 FRANTSAY")
    st.session_state.level = st.selectbox("Niveau", LEVELS, index=LEVELS.index(st.session_state.level))
    st.session_state.api_key = st.text_input("Clé Gemini", type="password", value=st.session_state.api_key)
    st.divider()
    st.metric("Points", st.session_state.score)
    st.metric("Activités", st.session_state.questions_done)

st.markdown(f"""
<div class="hero">
    <h1>Bonjour ! Prêt à progresser ?</h1>
    <p>Application Bento Grid — Niveau {st.session_state.level}</p>
</div>
""", unsafe_allow_html=True)

tab_home, tab_correction, tab_pron, tab_missions = st.tabs(
    ["🏠 Parcours", "✍️ Correction", "🎙️ Atelier Vocal (Micro)", "🗣️ Missions"]
)

with tab_home:
    st.markdown('<div class="bento-card"><h3>📘 Leçons du jour</h3></div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, lesson in enumerate([x for x in LESSONS if x["niveau"] in ["Tous", st.session_state.level]]):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="bento-card">
                <h4>{lesson['titre']}</h4>
                <p>{lesson['contenu']}</p>
                <small><b>Exemple :</b> {lesson['exemple']}</small>
            </div>
            """, unsafe_allow_html=True)

with tab_pron:
    st.markdown('<div class="bento-card"><h3>🎙️ Entraînement à la Prononciation avec Micro</h3><p>Écoutez le modèle, puis enregistrez votre voix pour recevoir une correction de l\'IA.</p></div>', unsafe_allow_html=True)
    
    for idx, item in enumerate(PRONUNCIATION):
        with st.container():
            st.markdown(f"#### {item['titre']}")
            st.caption(item["explication"])
            
            for j, (a, b) in enumerate(item["paires"]):
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    st.write(f"**{a}** vs **{b}**")
                    if st.button("🔊 Écouter", key=f"tts_{idx}_{j}"):
                        st.audio(make_audio(f"{a}. {b}."), format="audio/mp3")
                with c2:
                    st.write("🎙️ **Enregistrer :**")
                    recorded_audio = audio_recorder(key=f"rec_{idx}_{j}", recording_color="#6366F1", neutral_color="#64748B")
                with c3:
                    if recorded_audio:
                        st.audio(recorded_audio, format="audio/wav")
                        if api_available():
                            if st.button("✨ Corriger la prononciation", key=f"eval_{idx}_{j}"):
                                with st.spinner("Analyse par l'IA..."):
                                    feedback = analyze_pronunciation_audio(recorded_audio, f"{a} {b}")
                                    st.info(feedback)
                        else:
                            st.warning("Ajoutez votre clé Gemini pour la correction vocale.")
            st.divider()

with tab_correction:
    st.markdown('<div class="bento-card"><h3>✍️ Analyse de texte</h3></div>', unsafe_allow_html=True)
    user_text = st.text_area("Votre phrase :", placeholder="Hier je suis allé au marché...")
    if st.button("Analyser la phrase") and api_available():
        res = call_gemini("Tu es un prof FLE à Madagascar. Réponds en JSON structuré.", user_text)
        st.write(res)

with tab_missions:
    st.markdown('<div class="bento-card"><h3>🗣️ Mises en situation</h3></div>', unsafe_allow_html=True)
    mission_name = st.selectbox("Choisir une mission", [m[0] for m in MISSIONS])
    if st.button("Générer le dialogue") and api_available():
        res = call_gemini("Génère un dialogue de mise en situation à Madagascar.", mission_name)
        st.markdown(res)
    
