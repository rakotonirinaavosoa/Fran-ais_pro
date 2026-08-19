# -*- coding: utf-8 -*-
"""
FRANTSAY — Plateforme d'apprentissage du français pour les élèves et étudiants à Madagascar.
Design : Light Mode "Vercel" — Optimisé Mobile — Sans emoji, iconographie minimaliste en texte.
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
MODEL_NAME = "gemini-3.6-flash"
LEVELS = ["Collège", "Lycée", "Université"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le français",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# 2. DESIGN — VERCEL STYLE, COMPACT MOBILE (CSS)
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600&display=swap');

:root {
    --bg: #FAFAFA;
    --card: #FFFFFF;
    --ink: #0F172A;
    --muted: #64748B;
    --line: #E2E8F0;
    --purple: #4F46E5;
    --purple-soft: #EEF2FF;
    --green: #10B981;
    --red: #EF4444;
    --radius: 16px;
    --footer-h: 46px;
}

html, body, [class*="css"] {
    font-family: "Plus Jakarta Sans", "Inter", sans-serif;
}

.stApp { background: var(--bg); color: var(--ink); }
h1, h2, h3, h4, h5, p, span, label, div { color: var(--ink); }

.block-container {
    max-width: 700px;
    padding-top: .8rem;
    padding-bottom: calc(var(--footer-h) + 1.4rem);
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
    background: var(--purple-soft);
    color: var(--purple);
    border: 1px solid #DDD6FE;
}
.tag-solid { background: var(--purple); color: #fff; border-color: var(--purple); }
.tag-green { background: #ECFDF5; color: #047857; border-color: #A7F3D0; }
.tag-red { background: #FEF2F2; color: #B91C1C; border-color: #FECACA; }

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
    font-size: .66rem;
    color: var(--muted);
}
.stTabs [aria-selected="true"] { background: var(--purple) !important; color: white !important; }

section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid var(--line); }

/* Canal caché JS -> Streamlit pour le retour de l'audio enregistré (voir Module 03) */
.st-key-audio_bridge_slot { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }

/* Footer fixe, toujours visible quel que soit l'onglet ouvert */
.app-footer {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    height: var(--footer-h);
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,.92);
    backdrop-filter: blur(6px);
    border-top: 1px solid var(--line);
    color: #94A3B8;
    font-size: .72rem;
    z-index: 999;
}
.app-footer b { color: var(--muted); font-weight: 700; }

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

RECORDER_HTML = """
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
  #rec-wrap { font-family: "Plus Jakarta Sans", "Inter", sans-serif; }
  .rec-row { display: flex; gap: 8px; margin-bottom: 10px; }
  .rec-btn {
    flex: 1; border: 0; border-radius: 12px; padding: 12px 10px;
    font-weight: 700; font-size: 13px; cursor: pointer;
    transition: transform .15s ease, opacity .15s ease;
  }
  .rec-btn:active { transform: scale(0.97); }
  .rec-btn:disabled { opacity: .4; cursor: not-allowed; }
  .rec-start { background: #4F46E5; color: #fff; box-shadow: 0 4px 12px rgba(79,70,229,.28); }
  .rec-stop { background: #EF4444; color: #fff; box-shadow: 0 4px 12px rgba(239,68,68,.28); }
  .rec-meta {
    display: flex; align-items: center; gap: 8px;
    font-size: 12px; color: #64748B; padding: 2px 2px;
  }
  .rec-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #CBD5E1; flex: none;
  }
  .rec-dot.live { background: #EF4444; box-shadow: 0 0 0 0 rgba(239,68,68,.6); animation: pulse 1.1s infinite; }
  @keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(239,68,68,.55); }
    70% { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
  }
  .rec-status { flex: 1; }
  .rec-timer { font-family: "JetBrains Mono", monospace; font-weight: 700; color: #0F172A; }
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


# =============================================================================
# 9. BARRE LATÉRALE (SIDEBAR) — sans champ de saisie de clé API
# =============================================================================

with st.sidebar:
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
# 10. EN-TÊTE (compact, sans bloc de statistiques)
# =============================================================================

status = (
    '<span class="badge badge-ok"><span class="dot"></span>Assistant IA actif</span>'
    if api_available()
    else '<span class="badge badge-warn">Cours disponibles · IA non activée</span>'
)

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow"><span class="tag tag-solid">MG</span> Français pour tous.</div>
        <h1>Prêt à progresser en français ?</h1>
        <p>Comprends, pratique, écoute et ose parler — niveau {safe_html(level)}.</p>
        <div style="margin-top:.5rem">{status}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# 11. ONGLETS ET MODULES
# =============================================================================

tab_home, tab_correction, tab_missions, tab_pron, tab_quiz = st.tabs(
    ["Accueil", "01 · Grammaire", "02 · Missions", "03 · Prononciation", "04 · Quiz"]
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

    components.html(RECORDER_HTML, height=110, scrolling=False)

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
