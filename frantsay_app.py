# -*- coding: utf-8 -*-
"""
FRANTSAY — Plateforme d'apprentissage du français pour Madagascar.
Design : Bento Grid Modern (Pastel, Violet/Orange, Ultra-arrondi)
Fonctionnalité clé : Enregistrement vocal et correction phonétique par Gemini.
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
# 1. CONFIGURATION & AUTHENTIFICATION
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
# 2. DESIGN — BENTO GRID (Inspiré de l'image)
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-base: #FFFBF7;
    --card-white: #FFFFFF;
    --violet-main: #6366F1;
    --violet-light: #EEF2FF;
    --orange-main: #F59E0B;
    --orange-light: #FEF3C7;
    --text-dark: #1F2937;
    --text-muted: #6B7280;
    --radius-xl: 28px;
    --radius-md: 16px;
}

html, body, [class*="css"] {
    font-family: "Inter", sans-serif;
    background-color: var(--bg-base);
    color: var(--text-dark);
}

/* Fond général */
.stApp {
    background-color: var(--bg-base);
    background-image: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.05) 0%, transparent 40%);
}

/* Conteneur principal aéré */
.block-container {
    max-width: 1280px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* ---------- CARTES BENTO (Ultra arrondies) ---------- */
.bento-card {
    background: var(--card-white);
    border-radius: var(--radius-xl);
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.8);
    transition: transform 0.2s ease;
}

.bento-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.06);
}

.bento-card h3 { margin-top: 0; font-weight: 700; }
.bento-card .eyebrow {
    color: var(--violet-main);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.3rem;
    display: block;
}

/* ---------- BANNIÈRES VIOLET & ORANGE ---------- */
.banner-violet {
    background: linear-gradient(135deg, #818CF8 0%, #6366F1 100%);
    color: white;
    border-radius: var(--radius-xl);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.banner-violet h2, .banner-violet p { color: white; }
.banner-violet::after {
    content: "🇲🇬";
    position: absolute;
    right: 20px;
    bottom: 10px;
    font-size: 4rem;
    opacity: 0.2;
}

.banner-orange {
    background: linear-gradient(135deg, #FCD34D 0%, #F59E0B 100%);
    color: #78350F;
    border-radius: var(--radius-xl);
    padding: 1.2rem 2rem;
    margin-bottom: 1.5rem;
}

/* ---------- STATS BENTO ---------- */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.stat-item {
    background: var(--card-white);
    border-radius: var(--radius-xl);
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.04);
}
.stat-number { font-size: 1.8rem; font-weight: 800; color: var(--violet-main); }
.stat-label { color: var(--text-muted); font-size: 0.8rem; font-weight: 600; }

/* ---------- BOUTONS ---------- */
div.stButton > button {
    border: none;
    border-radius: var(--radius-xl);
    padding: 0.7rem 1.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--violet-main), #4F46E5);
    color: white;
    box-shadow: 0 5px 15px rgba(99, 102, 241, 0.3);
    transition: all 0.15s ease;
    width: 100%;
}
div.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}

/* ---------- CHAMPS ---------- */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: var(--radius-md) !important;
    border: 1px solid #E5E7EB !important;
    background: #F9FAFB !important;
}

/* ---------- AUDIO RECORDER ---------- */
/* Personnalisation du composant audio-recorder */
div[data-testid="stAudioRecorder"] {
    border-radius: var(--radius-xl);
    border: 1px dashed var(--violet-main);
    padding: 1rem;
    background: var(--violet-light);
    text-align: center;
    margin-bottom: 1rem;
}

/* ---------- BARRE LATÉRALE ---------- */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #F3F4F6;
}
section[data-testid="stSidebar"] .stMetric {
    background: #F9FAFB;
    border-radius: var(--radius-md);
    padding: 0.8rem;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# 3. DONNÉES PÉDAGOGIQUES (INTÉGRALEMENT CONSERVÉES)
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
    "last_audio_analysis": None,
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
        '<div class="banner-orange"><b>🔑 Activer l\'IA :</b> Ajoute ta clé Gemini dans la barre latérale pour profiter de la correction vocale et des quiz intelligents.</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# 6. PROMPTS (Intégration du prompt vocal)
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

# NOUVEAU PROMPT : Analyse vocale
AUDIO_PROMPT = """
Tu es un professeur de phonétique française.
L'utilisateur t'envoie un enregistrement vocal pour évaluer sa prononciation.
Analyse la clarté, la nasalité, les liaisons et les sons spécifiques.
Réponds uniquement en JSON :
{
  "score": 0-100,
  "points_forts": ["..."],
  "points_a_ameliorer": ["..."],
  "conseil_pratique": "..."
}
"""


# =============================================================================
# 7. SIDEBAR (Overlay clair)
# =============================================================================

with st.sidebar:
    st.markdown("## 🇲🇬 FRANTSAY")
    st.caption("Design Bento Grid")

    st.markdown("### 🎓 Niveau")
    level = st.selectbox(
        "Niveau",
        LEVELS,
        index=LEVELS.index(st.session_state.level),
        label_visibility="collapsed",
    )
    st.session_state.level = level

    st.divider()

    st.markdown("### 🔑 IA")
    manual_key = st.text_input(
        "Clé Gemini",
        type="password",
        value=st.session_state.api_key,
        placeholder="AIza...",
        help="L'app reste utilisable sans clé, mais l'IA vocale ne fonctionnera pas.",
    )
    st.session_state.api_key = manual_key

    if api_available():
        st.success("IA connectée")
    else:
        st.warning("IA en attente")

    st.divider()

    st.markdown("### 📈 Progression")
    st.metric("Points", st.session_state.score)
    st.metric("Activités", st.session_state.questions_done)


# =============================================================================
# 8. HEADER & STATS BENTO
# =============================================================================

st.markdown(
    """
    <div class="banner-violet">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin:0;">Bonjour !</h1>
        <p style="font-size: 1.1rem; margin:0.5rem 0 0;">Prêt à progresser en français ? Des leçons concrètes, des missions et un assistant vocal.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Stats Grid (Bento)
st.markdown(
    f"""
    <div class="stat-grid">
        <div class="stat-item"><div class="stat-number">{st.session_state.score}</div><div class="stat-label">Points</div></div>
        <div class="stat-item"><div class="stat-number">{st.session_state.questions_done}</div><div class="stat-label">Act. terminées</div></div>
        <div class="stat-item"><div class="stat-number" style="color:var(--orange-main);">🇲🇬</div><div class="stat-label">Local</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# 9. ONGLETS (Réorganisation : Parcours, Grammaire, Phonétique, Quiz)
# =============================================================================

tab_home, tab_correction, tab_audio, tab_quiz = st.tabs(
    ["📚 Parcours", "✍️ Correction", "🎙️ Prononciation", "🧠 Quiz"]
)


# =============================================================================
# TAB 1 : PARCOURS
# =============================================================================

with tab_home:
    st.markdown('<div class="bento-card"><span class="eyebrow">Parcours</span><h3>Apprendre sans se perdre</h3><p>Commence par une petite leçon, écoute les exemples, puis utilise l\'IA pour pratiquer.</p></div>', unsafe_allow_html=True)

    relevant = [x for x in LESSONS if x["niveau"] == "Tous" or x["niveau"] == level]

    cols = st.columns(2)
    for i, lesson in enumerate(relevant):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="bento-card" style="padding:1.2rem;">
                    <b>📘 {safe_html(lesson["titre"])}</b>
                    <p style="font-size:0.9rem; margin:0.5rem 0;">{safe_html(lesson["contenu"])}</p>
                    <b style="color:var(--violet-main);">Exemple :</b> {safe_html(lesson["exemple"])}
                </div>
                """,
                unsafe_allow_html=True,
            )


# =============================================================================
# TAB 2 : CORRECTION (Texte + Vocal)
# =============================================================================

with tab_correction:
    st.markdown('<div class="bento-card"><span class="eyebrow">Module 01</span><h3>Corrige ma phrase</h3><p>Écris ta phrase ou enregistre-toi. L\'IA structure et corrige.</p></div>', unsafe_allow_html=True)

    if not api_available():
        show_api_notice()

    text = st.text_area(
        "Phrase écrite",
        placeholder="Exemple : Hier, je suis allé au marché avec mes amis.",
        height=100,
    )

    if st.button("✍️ Analyser la phrase", key="analyze_text"):
        if not text.strip():
            st.warning("Écris d'abord une phrase.")
        elif not api_available():
            show_api_notice()
        else:
            try:
                with st.spinner("Analyse en cours..."):
                    raw = call_gemini(CORRECTION_PROMPT, f"Niveau : {level}\nPhrase : {text}")
                    result = extract_json(raw)
                st.session_state.last_correction = result
                st.session_state.questions_done += 1
                st.session_state.score += 5
            except Exception as exc:
                st.error(f"Erreur : {exc}")

    # Affichage du résultat texte
    if st.session_state.last_correction:
        res = st.session_state.last_correction
        st.markdown(f'<div class="bento-card"><h4>✅ Phrase corrigée</h4><h4 style="color:var(--violet-main);">{safe_html(res.get("phrase_corrigee", ""))}</h4></div>', unsafe_allow_html=True)
        st.write(res.get("explication", ""))
        errors = res.get("erreurs", [])
        for err in errors:
            st.markdown(f"- **{err.get('erreur','')}** → {err.get('correction','')}  \n  *{err.get('raison','')}*")


# =============================================================================
# TAB 3 : PRONONCIATION (Audio Recorder + gTTS)
# =============================================================================

with tab_audio:
    st.markdown('<div class="bento-card"><span class="eyebrow">Module 02</span><h3>Atelier Phonétique</h3><p>Écoute les sons, puis enregistre-toi pour obtenir un retour IA sur ta prononciation.</p></div>', unsafe_allow_html=True)

    # 1. Exercices classiques gTTS
    for idx, item in enumerate(PRONUNCIATION):
        with st.expander(f"🔊 {item['titre']}", expanded=(idx==0)):
            st.write(item["explication"])
            cols = st.columns(len(item["paires"]))
            for j, (a, b) in enumerate(item["paires"]):
                with cols[j]:
                    st.markdown(f"**{a}** ↔ **{b}**")
                    if st.button("🔊 Écouter", key=f"listen_{idx}_{j}"):
                        try:
                            st.audio(make_audio(a, slow=True), format="audio/mp3")
                            st.audio(make_audio(b, slow=True), format="audio/mp3")
                        except Exception as exc:
                            st.error(f"Audio indisponible : {exc}")

    st.divider()

    # 2. Enregistrement vocal avec Audio Recorder
    st.markdown("### 🎙️ Teste ta prononciation (Micro)")
    st.caption("Appuie sur le bouton, lis une phrase (ex: 'Bonjour, je suis étudiant'), et reçois un retour IA.")

    audio_bytes = audio_recorder(
        text="Clique pour enregistrer",
        recording_color="#e8b62b",
        neutral_color="#6aa36f",
        icon_name="microphone",
        sample_rate=16000,
    )

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        if st.button("🔬 Analyser ma prononciation", key="analyze_audio"):
            if not api_available():
                show_api_notice()
            else:
                try:
                    with st.spinner("Évaluation phonétique par Gemini..."):
                        # Important : Gemini accepte les bytes audio directement via l'API "files"
       from google import genai
                        client = genai.Client(api_key=get_api_key())
                        
                        # Upload du fichier audio en mémoire
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=[
                                "Analyse la prononciation de cet enregistrement vocal. Réponds uniquement en JSON avec score, points forts, points à améliorer et conseil.",
                                genai.upload_file(io.BytesIO(audio_bytes), mime_type="audio/wav")
                            ],
                        )
                        result = extract_json(response.text)
                        
                        st.session_state.last_audio_analysis = result
                        st.session_state.questions_done += 1
                        st.session_state.score += 10
                except Exception as exc:
                    st.error(f"Erreur d'analyse audio : {exc}")
   # Affichage du résultat vocal
    if st.session_state.last_audio_analysis:
        analysis = st.session_state.last_audio_analysis
        score = analysis.get("score", 0)
        st.markdown(f"""
        <div class="bento-card" style="border: 1px solid var(--violet-main);">
            <h4>📊 Score de prononciation : {score}/100</h4>
            <div style="background:#E5E7EB; height:8px; border-radius:999px; width:100%; margin:1rem 0;">
                <div style="background:linear-gradient(90deg, #F59E0B, #6366F1); height:8px; border-radius:999px; width:{score}%;"></div>
        </div>
            <b>Points forts :</b><br>
            {"".join([f"• {p}<br>" for p in analysis.get("points_forts", [])])}
            <br><b>Points à améliorer :</b><br>
            {"".join([f"• {p}<br>" for p in analysis.get("points_a_ameliorer", [])])}
            <br><b>💡 Conseil :</b> {analysis.get("conseil_pratique", "")}
        </div>
        """, unsafe_allow_html=True)
        #=============================================================================
        # TAB 4 : QUIZ
        #=============================================================================
        with tab_quiz:
    st.markdown('<div class="bento-card"><span class="eyebrow">Module 04</span><h3>Quiz intelligent</h3><p>Une question à la fois. Après ta réponse, tu reçois une explication.</p></div>', unsafe_allow_html=True)

    if "quiz_question" not in st.session_state:
        st.session_state.quiz_question = None

    if st.session_state.quiz_question is None:
        if api_available():
            if st.button("🧠 Générer une question", key="new_quiz"):
                try:
                    with st.spinner("Préparation de la question..."):
                        raw = call_gemini(QUIZ_PROMPT, f"Niveau : {level}.")
                        st.session_state.quiz_question = extract_json(raw)
                        st.session_state.quiz_feedback = ""
                        st.rerun()
                except Exception as exc:
                    st.error(f"Erreur : {exc}")
        else:
            show_api_notice()
    else:

        show_api_notice()
    else:
        q = st.session_state.quiz_question
        st.markdown(f"### {q.get('question', '')}")
        options = q.get("options", [])

        answer = st.radio("Choisis une réponse", options, index=None, key="quiz_answer")

        if st.button("Valider", key="validate_quiz"):
            if answer is None:
                st.warning("Choisis une réponse.")
            else:
                correct_index = int(q.get("bonne_reponse", 0))
                correct = options[correct_index] if options else ""
                if answer == correct:
                    st.success("🎉 Bonne réponse !")
                    st.session_state.score += 10
                else:
                    st.error(f"Pas tout à fait. La bonne réponse était : {correct}")
                st.info(q.get("explication", ""))
                st.session_state.questions_done += 1
                st.session_state.quiz_question = None

        if st.button("Nouvelle question", key="reset_quiz"):
            st.session_state.quiz_question = None
            st.rerun()

        
        
