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
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions
from streamlit_cookies_controller import CookieController
from cryptography.fernet import Fernet, InvalidToken


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

APP_NAME = "FRANTSAY"
MODEL_NAME = "gemini-2.5-flash"
SESSION_COOKIE_NAME = "frantsay_sid"
SESSION_MAX_AGE = 60 * 60 * 24 * 30
LEVELS = ["Collège", "Lycée", "Université"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le français",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# 1bis. MASCOTTE ROBOT — SVG inline, adaptatif aux thèmes clair/sombre
# =============================================================================
# Aucune dépendance externe : le SVG est injecté directement dans le DOM via
# st.markdown(unsafe_allow_html=True), ce qui permet à ses couleurs (fill,
# stroke) de lire les variables CSS --purple/--violet/--card/--line/--robot-eye
# définies dans :root et donc de suivre automatiquement le thème actif.

ROBOT_SVG = """<svg class="hero-robot-svg" viewBox="0 0 100 108" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mascotte robot FRANTSAY" tabindex="0">
<defs>
<linearGradient id="robotBodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="var(--purple)" />
<stop offset="100%" stop-color="var(--indigo)" />
</linearGradient>
</defs>
<line x1="50" y1="14" x2="50" y2="3" stroke="var(--purple)" stroke-width="3" stroke-linecap="round" />
<circle class="robot-antenna-dot" cx="50" cy="3" r="4" fill="var(--robot-eye)" />
<circle cx="12" cy="58" r="6" fill="var(--violet)" />
<circle cx="88" cy="58" r="6" fill="var(--violet)" />
<circle cx="50" cy="58" r="42" fill="url(#robotBodyGrad)" />
<circle cx="50" cy="60" r="31" fill="var(--card)" stroke="var(--line)" stroke-width="1.5" />
<circle class="robot-eye" cx="38" cy="58" r="6.5" fill="var(--robot-eye)" />
<circle class="robot-eye" cx="62" cy="58" r="6.5" fill="var(--robot-eye)" />
<circle cx="40" cy="55.5" r="1.7" fill="#FFFFFF" opacity=".9" />
<circle cx="64" cy="55.5" r="1.7" fill="#FFFFFF" opacity=".9" />
<path d="M 39 76 Q 50 84 61 76" stroke="var(--robot-eye)" stroke-width="3.2" stroke-linecap="round" fill="none" opacity=".8" />
</svg>"""

# Interactivité du clic sur la mascotte robot : un vrai gestionnaire JS (plutôt
# qu'un attribut onclick inline) force un reflow avant de réappliquer la
# classe "robot-clicked", afin que chaque clic — même rapproché — relance bien
# l'animation robotClickBounce. Le binding est retenté tant que le SVG n'est
# pas encore monté (composant asynchrone), ce qui le rend valable aussi bien
# pour l'exemplaire de l'écran d'identification que pour celui de l'en-tête
# principal : un seul des deux est jamais présent dans le DOM à la fois.
ROBOT_CLICK_JS = """
<script>
(function() {
    var win = window.parent || window;
    var doc = win.document;
    var attemptsLeft = 20;

    function bindRobot() {
        var el = doc.querySelector('.hero-robot-svg');
        if (!el) {
            attemptsLeft -= 1;
            if (attemptsLeft > 0) { setTimeout(bindRobot, 150); }
            return;
        }
        if (el.dataset.frantsayBound === "1") { return; }
        el.dataset.frantsayBound = "1";

        function bounce() {
            el.classList.remove('robot-clicked');
            // Force le reflow : sans cette ligne, ré-ajouter une classe déjà
            // présente (clic rapide pendant l'animation en cours) ne relance
            // pas l'animation CSS robotClickBounce.
            void el.offsetWidth;
            el.classList.add('robot-clicked');
        }

        el.addEventListener('click', bounce);
        el.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); bounce(); }
        });
        el.addEventListener('animationend', function(e) {
            if (e.animationName === 'robotClickBounce') {
                el.classList.remove('robot-clicked');
            }
        });
    }

    bindRobot();
})();
</script>
"""

# Le thème doit être connu AVANT de construire le CSS. Le sélecteur visuel
# (st.radio) est rendu plus bas, tout en haut de la sidebar ; ici on ne fait
# que garantir que la clé existe pour ce rerun.
if "theme" not in st.session_state:
    st.session_state.theme = "light"


# =============================================================================
# 2. DESIGN — PALETTES CLAIR / SOMBRE (CSS piloté par st.session_state["theme"])
# =============================================================================

LIGHT_THEME = {
    # Palette rééquilibrée : bleu profond comme couleur d'action principale,
    # slate pour les neutres, indigo/violet réduits à de simples touches
    # d'accent (mascotte, une carte sur quatre), vert et ambre plus présents.
    "bg": "#F8FAFC", "card": "#FFFFFF", "ink": "#0F172A", "muted": "#64748B", "line": "#E2E8F0",
    "purple": "#2563EB", "violet": "#7C3AED", "indigo": "#4F46E5",
    "green": "#059669", "amber": "#D97706", "red": "#DC2626",
    "soft_purple_bg": "#EFF6FF", "soft_purple_border": "#BFDBFE",
    "soft_indigo_bg": "#EEF2FF", "soft_indigo_border": "#C7D2FE",
    "soft_green_bg": "#ECFDF5", "soft_green_border": "#A7F3D0", "soft_green_text": "#047857",
    "soft_amber_bg": "#FFFBEB", "soft_amber_border": "#FDE68A", "soft_amber_text": "#B45309",
    "soft_red_bg": "#FEF2F2", "soft_red_border": "#FECACA", "soft_red_text": "#B91C1C",
    "tabs_bg": "#F1F5F9", "shadow_rgb": "15,23,42", "hero_end": "#EFF6FF",
    "footer_bg": "rgba(255,255,255,.92)", "scheme": "light", "robot_eye": "#059669",
}
DARK_THEME = {
    "bg": "#0B1220", "card": "#141E30", "ink": "#F1F5F9", "muted": "#94A3B8", "line": "#25314A",
    "purple": "#3B82F6", "violet": "#A78BFA", "indigo": "#818CF8",
    "green": "#34D399", "amber": "#FBBF24", "red": "#F87171",
    "soft_purple_bg": "#152238", "soft_purple_border": "#2A3F63",
    "soft_indigo_bg": "#1B2140", "soft_indigo_border": "#37408A",
    "soft_green_bg": "#0F2E24", "soft_green_border": "#1F5C46", "soft_green_text": "#6EE7B7",
    "soft_amber_bg": "#332408", "soft_amber_border": "#6B4A1E", "soft_amber_text": "#FBBF24",
    "soft_red_bg": "#3A1620", "soft_red_border": "#6B2331", "soft_red_text": "#FCA5A5",
    "tabs_bg": "#162035", "shadow_rgb": "0,0,0", "hero_end": "#13203A",
    "footer_bg": "rgba(20,30,48,.92)", "scheme": "dark", "robot_eye": "#34D399",
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
    --indigo: {theme['indigo']};
    --green: {theme['green']};
    --amber: {theme['amber']};
    --red: {theme['red']};
    --soft-purple-bg: {theme['soft_purple_bg']};
    --soft-purple-border: {theme['soft_purple_border']};
    --soft-indigo-bg: {theme['soft_indigo_bg']};
    --soft-indigo-border: {theme['soft_indigo_border']};
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
    --robot-eye: {theme['robot_eye']};
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

html { scroll-behavior: smooth; }
* { -webkit-tap-highlight-color: transparent; }

.stApp { background: var(--bg); color: var(--ink); transition: background-color .25s ease, color .25s ease; }
h1, h2, h3, h4, h5, p, span, label, div { color: var(--ink); }

.block-container {
    max-width: 700px;
    padding-top: 1.3rem;
    padding-bottom: calc(var(--footer-h) + 1.4rem);
    padding-left: .9rem;
    padding-right: .9rem;
    transition: max-width .2s ease;
}

/* Confort de lecture / respiration accrue sur tablette et desktop, sans
   changer la structure : le conteneur s'élargit et les cartes gagnent un
   peu d'air pour rester agréables au-delà du mobile. */
@media (min-width: 768px) {
    .block-container { max-width: 760px; padding-top: 1.8rem; }
    .card, .lesson { padding: 1rem 1.15rem; }
}
@media (min-width: 1100px) {
    .block-container { max-width: 820px; }
}

/* Respecte les préférences d'accessibilité : coupe les animations non
   essentielles si l'utilisateur a demandé une réduction du mouvement. */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}

/* Cartes Vercel : bord fin, radius 16px, transition douce au changement de thème */
.card, .lesson, .tip, .mini, .st-key-hero_box {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: 0 4px 14px -6px rgba(var(--shadow-rgb), 0.06);
    transition: transform .2s cubic-bezier(.16,1,.3,1), box-shadow .2s cubic-bezier(.16,1,.3,1),
                background-color .25s ease, border-color .25s ease;
    will-change: transform;
}

/* Le hover n'est appliqué que sur les appareils à pointeur précis (souris) :
   sur tactile, un hover "collant" gêne plus qu'il n'aide. */
@media (hover: hover) and (pointer: fine) {
    .card:hover, .lesson:hover { transform: translateY(-2px); box-shadow: 0 12px 26px -10px rgba(var(--shadow-rgb),.14); border-color: var(--purple); }
}
.card:active, .lesson:active { transform: scale(.985); }

.st-key-hero_box {
    padding: 1rem 1.1rem;
    margin-bottom: .7rem;
    background: linear-gradient(135deg, var(--card) 0%, var(--hero-end) 100%);
    overflow: hidden;
    position: relative;
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

/* Ligne badge de statut + mascotte, robot toujours à droite du badge,
   quelle que soit la largeur d'écran (flex, pas de colonnes Streamlit
   qui s'empilent sur mobile). */
.hero-status-row {
    margin-top: .5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: .6rem;
}

/* Écran d'identification (e-mail + pseudo) — bandeau dégradé immersif avec
   la mascotte robot, dans le même esprit que l'en-tête principal mais en
   plus marqué, pour que ce premier contact avec l'appli ne soit plus un
   simple formulaire nu. */
.st-key-auth_hero {
    background: linear-gradient(135deg, var(--purple) 0%, var(--indigo) 55%, var(--violet) 100%);
    border: none;
    border-radius: var(--radius);
    padding: 1.3rem 1.2rem;
    margin-bottom: .7rem;
    box-shadow: 0 14px 30px -12px rgba(37,99,235,.45);
    overflow: hidden;
}
.st-key-auth_hero [data-testid="stVerticalBlockBorderWrapper"] { background: transparent; border: 0; }
.auth-hero-row { display: flex; align-items: center; gap: 1rem; }
.auth-hero-row .hero-robot-svg { width: clamp(56px, 18vw, 78px); flex: none; }
.auth-hero-title { color: #fff !important; font-size: clamp(1.15rem, 4.8vw, 1.55rem); font-weight: 800; letter-spacing: -.5px; margin: .25rem 0 .15rem 0; line-height: 1.18; }
.auth-hero-sub { color: rgba(255,255,255,.85) !important; margin: 0; font-size: .82rem; }

/* Aperçu coloré des quatre modules, pour donner un avant-goût de l'appli
   avant même de créer son profil (mêmes teintes que les onglets). */
.auth-features { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0 0 .8rem 0; }

.auth-form-card { margin-bottom: .6rem; }

/* Mascotte robot SVG — s'adapte au thème via les variables CSS (--purple,
   --violet, --card, --line, --robot-eye), animée légèrement pour un rendu
   vivant et immersif sans jamais distraire de l'essentiel. */
.hero-robot-svg {
    width: clamp(38px, 11vw, 52px);
    flex: none;
    display: block;
    cursor: pointer;
    filter: drop-shadow(0 6px 14px rgba(var(--shadow-rgb), .2));
    animation: robotFloat 3.6s ease-in-out infinite;
}
.hero-robot-svg.robot-clicked {
    /* Une seule animation à la fois sur "transform" : en superposant robotFloat
       et robotClickBounce, le navigateur ne restituait que la dernière de la
       liste et le rebond au clic devenait invisible. On remplace donc le flottement
       par le rebond pendant sa durée ; robotFloat reprend seul dès la fin du rebond
       (retour à la règle de base ci-dessus, dès que la classe est retirée). */
    animation: robotClickBounce .6s cubic-bezier(.34,1.56,.64,1);
}
@keyframes robotClickBounce {
    0% { transform: scale(1) rotate(0deg); }
    30% { transform: scale(1.18) rotate(-10deg); }
    55% { transform: scale(.93) rotate(8deg); }
    80% { transform: scale(1.05) rotate(-3deg); }
    100% { transform: scale(1) rotate(0deg); }
}
@keyframes robotFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
}
.robot-eye {
    filter: drop-shadow(0 0 5px var(--robot-eye));
    animation: robotEyeGlow 2.4s ease-in-out infinite;
}
@keyframes robotEyeGlow {
    0%, 100% { opacity: 1; }
    50% { opacity: .6; }
}
.robot-antenna-dot {
    filter: drop-shadow(0 0 4px var(--robot-eye));
    animation: robotEyeGlow 1.8s ease-in-out infinite;
}

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
.tag-amber { background: var(--soft-amber-bg); color: var(--soft-amber-text); border-color: var(--soft-amber-border); }
.tag-muted { background: var(--tabs-bg); color: var(--muted); border-color: var(--line); }

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

.lesson { padding: .7rem .75rem; border-left: 3px solid var(--purple); }
.lesson b { font-size: .82rem; }
.lesson p { font-size: .76rem; margin: .25rem 0; color: var(--muted); }
/* Alternance de couleur sur les fiches de leçon, pour casser le "tout violet"
   et aider à repérer les fiches d'un coup d'oeil ; fonctionne en clair et en
   sombre car chaque teinte vient d'une variable de thème. */
.grid-2 .lesson:nth-child(4n+2) { border-left-color: var(--green); }
.grid-2 .lesson:nth-child(4n+3) { border-left-color: var(--amber); }
.grid-2 .lesson:nth-child(4n+4) { border-left-color: var(--violet); }

.tip { background: var(--soft-purple-bg); border-color: var(--soft-purple-border); padding: .7rem .8rem; font-size: .8rem; }

.capsule {
    display: inline-flex; flex-direction: column;
    border-radius: 12px; padding: .4rem .6rem; margin: .15rem .25rem .15rem 0;
    border: 1px solid; min-width: 90px;
}
.capsule-type { font-size: .55rem; font-weight: 800; text-transform: uppercase; letter-spacing: .4px; }
.capsule-text { font-weight: 700; margin-top: .1rem; font-size: .82rem; }

.sujet { background: var(--soft-indigo-bg); border-color: var(--soft-indigo-border); color: var(--indigo); }
.verbe { background: var(--soft-green-bg); border-color: var(--soft-green-border); color: var(--soft-green-text); }
.complement { background: var(--soft-amber-bg); border-color: var(--soft-amber-border); color: var(--soft-amber-text); }
.autre { background: var(--tabs-bg); border-color: var(--line); color: var(--muted); }

/* Phrase modèle — carte immersive */
.phrase-modele {
    background: linear-gradient(135deg, var(--purple) 0%, var(--indigo) 100%);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    color: white;
    margin-bottom: .6rem;
    box-shadow: 0 10px 24px -10px rgba(37,99,235,.5);
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
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28) !important;
    transition: transform .18s cubic-bezier(.16,1,.3,1), box-shadow .18s ease, filter .18s ease !important;
    width: 100%;
}
@media (hover: hover) and (pointer: fine) {
    div.stButton > button:hover { transform: scale(1.015); box-shadow: 0 6px 16px rgba(37, 99, 235, 0.38) !important; filter: brightness(1.05); }
}
div.stButton > button:active { transform: scale(0.97); }
div.stButton > button:focus-visible { outline: 2px solid var(--purple) !important; outline-offset: 2px; }

.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stFileUploader section {
    background: var(--card) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    transition: border-color .18s ease, box-shadow .18s ease !important;
}
.stTextInput input:focus, .stTextArea textarea:focus,
.stSelectbox div[data-baseweb="select"]:focus-within > div {
    border-color: var(--purple) !important;
    box-shadow: 0 0 0 3px var(--soft-purple-bg) !important;
}

/* Menu déroulant du selectbox (BaseWeb) : rendu dans un portail en dehors de
   .stApp, il n'héritait donc d'aucune règle ci-dessus et gardait un fond
   blanc figé avec du texte blanc en mode sombre (texte invisible). On cible
   directement le popover et ses options pour forcer les variables du thème
   courant, avec un état hover/sélectionné lisible dans les deux thèmes. */
div[data-baseweb="popover"],
div[data-baseweb="popover"] div[data-baseweb="menu"],
div[data-baseweb="popover"] ul[role="listbox"] {
    background: var(--card) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 26px -10px rgba(var(--shadow-rgb), .25) !important;
}
li[data-baseweb="option"] {
    background: var(--card) !important;
    color: var(--ink) !important;
}
li[data-baseweb="option"] * {
    color: inherit !important;
}
li[data-baseweb="option"]:hover,
li[data-baseweb="option"][aria-selected="true"] {
    background: var(--soft-purple-bg) !important;
    color: var(--purple) !important;
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
    transition: background-color .2s cubic-bezier(.16,1,.3,1), color .2s ease, transform .15s ease;
}
.stTabs [aria-selected="true"] { background: var(--purple) !important; color: white !important; }
@media (hover: hover) and (pointer: fine) {
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover { background: var(--tabs-bg); color: var(--purple); }
}
.stTabs [data-baseweb="tab-panel"] { animation: tabFadeIn .25s ease; }
@keyframes tabFadeIn { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }

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
.stTabs [data-baseweb="tab-list"] button:nth-of-type(2) p::before { content: "01"; color: var(--purple); }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(3) p::before { content: "02"; color: var(--green); }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(4) p::before { content: "03"; color: var(--amber); }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(5) p::before { content: "04"; color: var(--red); }
/* Chaque onglet garde la teinte de son badge une fois sélectionné, au lieu du
   violet unique appliqué partout : l'alternance de couleur reste lisible dans
   les deux thèmes clair et sombre grâce aux variables CSS --purple/--green/--amber/--red. */
.stTabs [data-baseweb="tab-list"] [aria-selected="true"] p::before { background: rgba(255,255,255,.9); border-color: transparent; }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(1) p::before { color: #fff; }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(2) p::before { color: var(--purple); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(3) p::before { color: var(--green); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(4) p::before { color: var(--amber); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(5) p::before { color: var(--red); }

section[data-testid="stSidebar"] { background: var(--card); border-right: 1px solid var(--line); }

/* Sélecteur de thème — sélecteur horizontal en haut de sidebar */
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex; gap: .35rem; background: var(--tabs-bg); padding: .3rem; border-radius: 12px;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    flex: 1; margin: 0 !important; padding: .3rem .4rem !important; border-radius: 9px;
    font-size: .74rem; font-weight: 700; justify-content: center;
    transition: background-color .2s cubic-bezier(.16,1,.3,1), color .2s ease;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
    background: var(--purple); color: #fff;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p { color: #fff !important; }

/* Canaux cachés JS -> Streamlit (audio du Module 03, progression du localStorage) */
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

/* ===================== FRANTSAY 2.0 — nouveau langage visuel ===================== */
.block-container { max-width: 1180px; padding-top: 1rem; padding-left: 1.2rem; padding-right: 1.2rem; }
.stApp { background:
    radial-gradient(circle at 8% 4%, rgba(124,58,237,.10), transparent 27%),
    radial-gradient(circle at 95% 10%, rgba(37,99,235,.09), transparent 25%), var(--bg); }

.st-key-auth_hero { background: linear-gradient(120deg, #081126 0%, #0E1530 52%, #102D68 100%); border-radius: 30px; padding: 2.1rem 2.2rem; margin-bottom: 1.25rem; box-shadow: 0 30px 70px rgba(15,23,42,.25); overflow:hidden; position:relative; }
.st-key-auth_hero:after { content:""; position:absolute; width:420px; height:420px; right:-150px; bottom:-240px; border:1px solid rgba(167,139,250,.18); border-radius:50%; box-shadow:0 0 0 35px rgba(167,139,250,.03),0 0 0 70px rgba(167,139,250,.02); }
.auth-shell { display:grid; grid-template-columns: 1.25fr .85fr; gap:2rem; position:relative; z-index:1; }
.auth-copy { color:#fff; min-height:360px; display:flex; flex-direction:column; justify-content:space-between; }
.brand-lockup { display:flex; align-items:center; gap:.7rem; }
.brand-lockup .hero-robot-svg { width:52px; }
.brand-name { color:#fff; font-size:1.55rem; font-weight:800; letter-spacing:-.8px; }
.brand-kicker { color:rgba(255,255,255,.48); font-size:.56rem; letter-spacing:1.5px; font-weight:700; margin-top:.12rem; }
.auth-copy-body { padding:1.7rem 0 1rem; max-width:610px; }
.auth-kicker { color:#A78BFA; font-size:.7rem; font-weight:800; letter-spacing:1.4px; text-transform:uppercase; margin-bottom:.55rem; }
.auth-main-title { color:#fff !important; font-size:clamp(2.15rem,5vw,3.45rem); line-height:1.02; letter-spacing:-1.8px; margin:0; font-weight:800; }
.auth-main-title span { background:linear-gradient(90deg,#A78BFA,#60A5FA); -webkit-background-clip:text; background-clip:text; color:transparent !important; }
.auth-main-sub { color:rgba(255,255,255,.68) !important; font-size:.94rem; line-height:1.65; max-width:560px; margin:.9rem 0 0; }
.auth-feature-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:.55rem; max-width:680px; }
.auth-feature { border:1px solid rgba(255,255,255,.13); background:rgba(255,255,255,.055); border-radius:16px; padding:.8rem .72rem; backdrop-filter:blur(8px); }
.auth-feature b,.auth-feature span { display:block; color:#fff; }
.auth-feature b { font-size:.72rem; margin-top:.55rem; }
.auth-feature span { color:rgba(255,255,255,.48); font-size:.58rem; margin-top:.14rem; }
.feature-icon { width:27px;height:27px;border-radius:9px;display:flex;align-items:center;justify-content:center;background:rgba(129,140,248,.14);color:#A5B4FC;font:700 .58rem "JetBrains Mono";border:1px solid rgba(129,140,248,.25); }
.feature-icon.green{color:#6EE7B7;background:rgba(52,211,153,.10);border-color:rgba(52,211,153,.22)}
.feature-icon.amber{color:#FCD34D;background:rgba(251,191,36,.10);border-color:rgba(251,191,36,.22)}
.feature-icon.red{color:#FDA4AF;background:rgba(248,113,113,.10);border-color:rgba(248,113,113,.22)}
.auth-quote { display:flex; gap:.45rem; align-items:flex-start; color:rgba(255,255,255,.58); font-size:.75rem; line-height:1.55; padding-top:.8rem; }
.auth-quote span { color:#8B5CF6; font-size:2rem; line-height:.7; }
.auth-panel { min-height:360px; border-radius:22px; border:1px solid rgba(255,255,255,.12); background:linear-gradient(145deg,rgba(255,255,255,.075),rgba(255,255,255,.035)); box-shadow:inset 0 1px 0 rgba(255,255,255,.06); padding:1.4rem; display:flex; align-items:flex-end; }
.auth-panel-top { width:100%; display:flex; align-items:flex-start; justify-content:space-between; gap:.8rem; }
.auth-welcome { color:#fff; font-size:1.15rem; font-weight:800; }
.auth-welcome-sub { color:rgba(255,255,255,.55); font-size:.72rem; margin-top:.2rem; }
.secure-pill { color:#A7F3D0; border:1px solid rgba(52,211,153,.22); background:rgba(52,211,153,.08); padding:.35rem .55rem; border-radius:999px; font-size:.58rem; white-space:nowrap; }
.secure-dot { display:inline-block; width:6px;height:6px;border-radius:50%;background:#34D399;box-shadow:0 0 8px #34D399; }
.auth-form-title { font-size:1.25rem; font-weight:800; letter-spacing:-.5px; margin-bottom:.2rem; }
.auth-form-subtitle { color:var(--muted); font-size:.78rem; margin-bottom:.8rem; }
.auth-side-card { background:linear-gradient(145deg,var(--card),var(--soft-purple-bg)); border:1px solid var(--line); border-radius:22px; padding:1.35rem; box-shadow:0 18px 45px rgba(var(--shadow-rgb),.08); margin-top:1.4rem; }
.side-card-icon { width:40px;height:40px;border-radius:13px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--purple),var(--violet));color:#fff;font-size:1.1rem;box-shadow:0 10px 22px rgba(79,70,229,.25); }
.side-card-title { font-weight:800;font-size:1.02rem;margin-top:.8rem; }
.auth-side-card p { color:var(--muted); font-size:.76rem; line-height:1.55; }
.side-check { display:flex;align-items:center;gap:.5rem;font-size:.7rem;font-weight:700;margin-top:.6rem; }
.side-check span { width:20px;height:20px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--soft-green-bg);color:var(--soft-green-text);border:1px solid var(--soft-green-border); }
.identity-note { display:flex;gap:.7rem;align-items:center;padding:.85rem .95rem;margin-top:.7rem;border:1px solid var(--line);background:var(--card);border-radius:17px; }
.identity-note-icon { width:34px;height:34px;border-radius:11px;display:flex;align-items:center;justify-content:center;background:var(--soft-purple-bg);color:var(--purple);font-size:1rem; }
.identity-note b { font-size:.72rem; }
.identity-note span { color:var(--muted);font-size:.64rem;line-height:1.45; }

.st-key-hero_box { background:transparent; border:0; padding:0; }
.dashboard-topline { display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:.3rem 0 1rem; }
.dashboard-topline .hero-title { margin:.25rem 0 .15rem; }
.wave { color:var(--purple); }
.hero-user-badge { display:flex; align-items:center; gap:.65rem; padding:.55rem .7rem; border:1px solid var(--line); background:var(--card); border-radius:16px; }
.hero-avatar { width:36px;height:36px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--purple),var(--violet));color:#fff;font-weight:800; }
.hero-user-badge b,.hero-user-badge span { display:block; }
.hero-user-badge b { font-size:.7rem; }
.hero-user-badge span { color:var(--muted); font-size:.58rem; max-width:170px; overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.dashboard-stat-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem;margin:.4rem 0 1rem; }
.dashboard-stat { background:var(--card);border:1px solid var(--line);border-radius:18px;padding:1rem;box-shadow:0 10px 25px rgba(var(--shadow-rgb),.045); }
.dashboard-stat.accent { background:linear-gradient(135deg,var(--purple),var(--violet));border-color:transparent; }
.dashboard-stat span,.dashboard-stat small { display:block; }
.dashboard-stat span { color:var(--muted);font:700 .55rem "JetBrains Mono";letter-spacing:.7px; }
.dashboard-stat b { display:block;font-size:1.25rem;letter-spacing:-.5px;margin:.28rem 0 .1rem; }
.dashboard-stat small { color:var(--muted);font-size:.58rem; }
.dashboard-stat.accent span,.dashboard-stat.accent b,.dashboard-stat.accent small { color:#fff; }

section[data-testid="stSidebar"] { background:#091221; border-right:1px solid rgba(148,163,184,.12); }
section[data-testid="stSidebar"] * { color:#E5E7EB; }
.sidebar-brand { display:flex;align-items:center;gap:.55rem;padding:.15rem .1rem 1rem; }
.sidebar-brand .hero-robot-svg { width:38px; }
.sidebar-brand strong { display:block;font-size:1rem;color:#fff;letter-spacing:-.3px; }
.sidebar-brand span { display:block;font-size:.55rem;color:#94A3B8;margin-top:.08rem; }
.sidebar-profile { display:flex;align-items:center;gap:.6rem;padding:.7rem;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.045);border-radius:15px;margin-bottom:1rem; }
.profile-avatar { width:32px;height:32px;border-radius:11px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;font-weight:800;font-size:.75rem; }
.sidebar-profile b,.sidebar-profile span { display:block; }
.sidebar-profile b { font-size:.7rem; }
.sidebar-profile span { font-size:.56rem;color:#94A3B8; }
.sidebar-section-label { color:#64748B !important;font:700 .55rem "JetBrains Mono";letter-spacing:1px;margin:.85rem .15rem .35rem; }
.sidebar-nav-item { padding:.55rem .65rem;border-radius:11px;color:#A8B2C4 !important;font-size:.68rem;font-weight:600;margin:.12rem 0; }
.sidebar-nav-item span { display:inline-flex;width:21px;color:#818CF8 !important; }
.sidebar-nav-item.active { color:#fff !important;background:linear-gradient(90deg,rgba(79,70,229,.95),rgba(124,58,237,.9));box-shadow:0 8px 20px rgba(79,70,229,.22); }
.sidebar-nav-item.active span { color:#fff !important; }
.sidebar-stats { display:grid;grid-template-columns:1fr 1fr;gap:.45rem;margin-top:.8rem; }
.sidebar-stats div { background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:13px;padding:.6rem; }
.sidebar-stats span { display:block;color:#64748B !important;font:700 .48rem "JetBrains Mono"; }
.sidebar-stats b { display:block;color:#fff !important;font-size:.9rem;margin-top:.15rem; }
section[data-testid="stSidebar"] div.stButton > button { background:transparent !important;border:1px solid rgba(248,113,113,.28) !important;color:#FCA5A5 !important;box-shadow:none !important;margin-top:1rem; }
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] { background:rgba(255,255,255,.05); }

@media (max-width: 850px) {
    .auth-shell { grid-template-columns:1fr; }
    .auth-panel { min-height:90px; }
    .auth-copy { min-height:0; }
    .auth-feature-grid { grid-template-columns:repeat(2,1fr); }
    .dashboard-stat-grid { grid-template-columns:repeat(2,1fr); }
    .dashboard-topline { align-items:flex-start; }
}
@media (max-width: 560px) {
    .block-container { padding-left:.65rem;padding-right:.65rem; }
    .st-key-auth_hero { padding:1.35rem 1rem;border-radius:22px; }
    .auth-main-title { font-size:2.15rem; }
    .auth-feature-grid { grid-template-columns:repeat(2,1fr); }
    .auth-panel { display:none; }
    .dashboard-topline { display:block; }
    .hero-user-badge { margin-top:.7rem; width:max-content; }
    .dashboard-stat-grid { grid-template-columns:repeat(2,1fr); }
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

# Parcours de défis par paliers (façon jeu vidéo) : chaque palier se
# débloque en cumulant des points (grammaire, missions, prononciation, quiz).
PALIERS = [
    (0, "Palier 1 — Premiers pas", "Termine ta première activité pour lancer l'aventure."),
    (20, "Palier 2 — Explorateur", "Continue à t'entraîner en grammaire et en missions."),
    (50, "Palier 3 — Apprenti confirmé", "Tu maîtrises les bases : attaque la prononciation."),
    (100, "Palier 4 — Orateur", "Enchaîne les quiz et les dialogues sans faute."),
    (200, "Palier 5 — Champion FRANTSAY", "Tu es prêt à parler français avec assurance !"),
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
# 5. ÉTAT DE SESSION + AUTHENTIFICATION SUPABASE
# =============================================================================

DEFAULT_STATE = {
    "level": "Lycée", "score": 0, "questions_done": 0,
    "last_correction": None, "last_dialogue": None,
    "quiz_question": None, "quiz_answer": None,
    "model_sentence": None, "pronunciation_result": None,
    "last_audio_hash": None, "user_email": None, "user_pseudo": None,
    "user_id": None, "auth_user_id": None, "access_token": None,
    "identified": False, "auth_view": "login",
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state: st.session_state[key] = value


def _secret(name: str, default: str = "") -> str:
    try: return str(st.secrets.get(name, default)).strip()
    except Exception: return default


@st.cache_resource(show_spinner=False)
def get_db_client() -> Client:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key: raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY manquant.")
    return create_client(url, key, options=ClientOptions(auto_refresh_token=False, persist_session=False))


def get_auth_client() -> Client:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_ANON_KEY")
    if not url or not key: raise RuntimeError("SUPABASE_URL ou SUPABASE_ANON_KEY manquant.")
    return create_client(url, key, options=ClientOptions(auto_refresh_token=False, persist_session=False))


def get_cookie_controller() -> CookieController:
    return CookieController(key="frantsay_auth_cookie")


def _fernet() -> Fernet:
    secret = _secret("SESSION_ENCRYPTION_KEY")
    if not secret: raise RuntimeError("SESSION_ENCRYPTION_KEY manquant dans les Secrets Streamlit.")
    try: return Fernet(secret.encode())
    except Exception as exc: raise RuntimeError("SESSION_ENCRYPTION_KEY doit être une clé Fernet valide.") from exc


def _hash_sid(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def _extract_first_row(response: Any) -> dict[str, Any] | None:
    data = getattr(response, "data", None) or []
    return data[0] if data else None


def supabase_ready() -> bool:
    try:
        get_db_client(); get_auth_client(); _fernet(); return True
    except Exception: return False


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._%+-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$")
PSEUDO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")

def normalize_email(email: str) -> str: return email.strip().lower()
def normalize_pseudo(pseudo: str) -> str: return re.sub(r"\s+", " ", pseudo.strip())
def is_valid_email(value: str) -> bool: return bool(EMAIL_PATTERN.fullmatch(value)) and ".." not in value
def is_valid_pseudo(value: str) -> bool: return bool(PSEUDO_PATTERN.fullmatch(value))


def find_profile_by_auth_id(auth_user_id: str) -> dict[str, Any] | None:
    return _extract_first_row(get_db_client().table("users").select("id,auth_user_id,email,pseudo,display_name,level,score,questions_done,progress").eq("auth_user_id", str(auth_user_id)).limit(1).execute())


def create_profile(auth_user_id: str, email: str, level: str, pseudo: str = "") -> dict[str, Any]:
    if level not in LEVELS: raise ValueError("Niveau invalide.")
    if pseudo and not is_valid_pseudo(pseudo): raise ValueError("Pseudo invalide : 3 à 24 caractères, lettres/chiffres/_/.- uniquement.")
    payload = {"auth_user_id": str(auth_user_id), "email": normalize_email(email), "display_name": normalize_pseudo(pseudo) if pseudo else None, "pseudo": normalize_pseudo(pseudo) if pseudo else None, "level": level, "score": 0, "questions_done": 0, "progress": {"score": 0, "questions_done": 0}}
    user = _extract_first_row(get_db_client().table("users").insert(payload).select("id,auth_user_id,email,pseudo,display_name,level,score,questions_done,progress").execute())
    if not user: raise RuntimeError("Le profil n'a pas pu être créé.")
    return user


def restore_profile(user: dict[str, Any], access_token: str) -> None:
    progress = user.get("progress") or {}
    level = str(user.get("level") or "")
    if level not in LEVELS: raise ValueError("Le profil ne possède pas un niveau d'études valide.")
    st.session_state.user_id = str(user["id"]); st.session_state.auth_user_id = str(user["auth_user_id"])
    st.session_state.user_email = str(user.get("email") or ""); st.session_state.user_pseudo = str(user.get("display_name") or user.get("pseudo") or "")
    st.session_state.level = level; st.session_state.score = int(progress.get("score", user.get("score", 0)) or 0)
    st.session_state.questions_done = int(progress.get("questions_done", user.get("questions_done", 0)) or 0)
    st.session_state.access_token = access_token; st.session_state.model_sentence = random.choice(MODEL_SENTENCES[level]); st.session_state.identified = True


def create_login_session(auth_user_id: str, refresh_token: str) -> None:
    session_id = uuid.uuid4().hex + uuid.uuid4().hex
    get_db_client().table("app_sessions").insert({"session_id_hash": _hash_sid(session_id), "auth_user_id": str(auth_user_id), "refresh_token_enc": _fernet().encrypt(refresh_token.encode()).decode(), "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}).execute()
    get_cookie_controller().set(SESSION_COOKIE_NAME, session_id, key="set_frantsay_sid", path="/", max_age=SESSION_MAX_AGE, secure=True, same_site="strict")


def delete_login_session(session_id: str | None) -> None:
    if not session_id: return
    try: get_db_client().table("app_sessions").delete().eq("session_id_hash", _hash_sid(session_id)).execute()
    finally:
        try: get_cookie_controller().delete(SESSION_COOKIE_NAME, key="delete_frantsay_sid")
        except Exception: pass


def restore_from_cookie() -> bool:
    try:
        sid = get_cookie_controller().get(SESSION_COOKIE_NAME)
        if not sid or not isinstance(sid, str): return False
        row = _extract_first_row(get_db_client().table("app_sessions").select("session_id_hash,auth_user_id,refresh_token_enc,expires_at").eq("session_id_hash", _hash_sid(sid)).limit(1).execute())
        if not row: return False
        expires_at = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
        if expires_at <= datetime.now(timezone.utc): delete_login_session(sid); return False
        refresh_token = _fernet().decrypt(str(row["refresh_token_enc"]).encode()).decode()
        auth = get_auth_client(); refreshed = auth.auth.refresh_session(refresh_token)
        session = getattr(refreshed, "session", None); user_obj = getattr(refreshed, "user", None)
        if not session or not user_obj: delete_login_session(sid); return False
        access_token = str(getattr(session, "access_token", "")); new_refresh = str(getattr(session, "refresh_token", ""))
        if not access_token or not new_refresh: delete_login_session(sid); return False
        verified = auth.auth.get_user(access_token); verified_user = getattr(verified, "user", None)
        if not verified_user or str(getattr(verified_user, "id", "")) != str(row["auth_user_id"]): delete_login_session(sid); return False
        get_db_client().table("app_sessions").update({"refresh_token_enc": _fernet().encrypt(new_refresh.encode()).decode(), "last_seen_at": datetime.now(timezone.utc).isoformat(), "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}).eq("session_id_hash", _hash_sid(sid)).execute()
        profile = find_profile_by_auth_id(str(row["auth_user_id"]))
        if not profile: delete_login_session(sid); return False
        restore_profile(profile, access_token); return True
    except (InvalidToken, Exception): return False


def sign_in(email: str, password: str) -> None:
    email = normalize_email(email)
    if not is_valid_email(email): raise ValueError("Saisis une adresse e-mail valide.")
    if len(password) < 8: raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
    response = get_auth_client().auth.sign_in_with_password({"email": email, "password": password})
    session = getattr(response, "session", None); user_obj = getattr(response, "user", None)
    if not session or not user_obj: raise ValueError("Connexion impossible. Vérifie ton e-mail et ton mot de passe.")
    access_token = str(getattr(session, "access_token", "")); refresh_token = str(getattr(session, "refresh_token", "")); auth_user_id = str(getattr(user_obj, "id", ""))
    profile = find_profile_by_auth_id(auth_user_id)
    if not access_token or not refresh_token or not auth_user_id or not profile: raise ValueError("Ton compte n'est pas correctement configuré dans FRANTSAY.")
    create_login_session(auth_user_id, refresh_token); restore_profile(profile, access_token)


def sign_up(email: str, password: str, confirm: str, pseudo: str, level: str) -> str:
    email = normalize_email(email); pseudo = normalize_pseudo(pseudo)
    if not is_valid_email(email): raise ValueError("Saisis une adresse e-mail valide.")
    if len(password) < 8: raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
    if password != confirm: raise ValueError("Les deux mots de passe ne correspondent pas.")
    if pseudo and not is_valid_pseudo(pseudo): raise ValueError("Pseudo invalide : 3 à 24 caractères, lettres/chiffres/_/.- uniquement.")
    if level not in LEVELS: raise ValueError("Choisis ton niveau d'études.")
    response = get_auth_client().auth.sign_up({"email": email, "password": password, "options": {"data": {"display_name": pseudo, "study_level": level}}})
    user_obj = getattr(response, "user", None); session = getattr(response, "session", None)
    if not user_obj: raise ValueError("L'inscription n'a pas pu être créée.")
    auth_user_id = str(getattr(user_obj, "id", ""))
    if find_profile_by_auth_id(auth_user_id): return "Compte déjà configuré. Confirme ton e-mail puis connecte-toi."
    create_profile(auth_user_id, email, level, pseudo)
    if session:
        access_token = str(getattr(session, "access_token", "")); refresh_token = str(getattr(session, "refresh_token", ""))
        if access_token and refresh_token:
            create_login_session(auth_user_id, refresh_token); restore_profile(find_profile_by_auth_id(auth_user_id), access_token); return "Compte créé. Bienvenue dans FRANTSAY."
    return "Compte créé. Vérifie ton e-mail avant de te connecter."


def current_progress() -> dict[str, Any]: return {"score": int(st.session_state.score), "questions_done": int(st.session_state.questions_done)}


def save_progress(user_id: str, data: dict[str, Any]) -> None:
    if not user_id: raise ValueError("user_id manquant.")
    score = max(0, int(data.get("score", 0))); done = max(0, int(data.get("questions_done", 0)))
    get_db_client().table("users").update({"score": score, "questions_done": done, "progress": {"score": score, "questions_done": done}, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", user_id).execute()


def save_current_progress() -> None:
    if not st.session_state.get("identified") or not st.session_state.get("user_id"): return
    try: save_progress(st.session_state.user_id, current_progress())
    except Exception as exc: st.warning(f"La progression n'a pas pu être synchronisée : {exc}")


def logout_user() -> None:
    sid = get_cookie_controller().get(SESSION_COOKIE_NAME); delete_login_session(sid)
    theme = st.session_state.get("theme", "light"); st.session_state.clear()
    for key, value in DEFAULT_STATE.items(): st.session_state[key] = value
    st.session_state.theme = theme; st.session_state.model_sentence = random.choice(MODEL_SENTENCES["Lycée"])


if not st.session_state.identified: restore_from_cookie()


def render_auth_screen() -> None:
    components.html(ROBOT_CLICK_JS, height=0)
    with st.container(key="auth_hero"):
        st.markdown(
            f'''<div class="auth-shell"><div class="auth-copy"><div class="brand-lockup">{ROBOT_SVG}<div><div class="brand-name">FRANTSAY</div><div class="brand-kicker">APPRENDRE · PRATIQUER · PROGRESSER</div></div></div><div class="auth-copy-body"><div class="auth-kicker">Ta nouvelle façon d'apprendre</div><h1 class="auth-main-title">Apprendre le français<br><span>autrement.</span></h1><p class="auth-main-sub">Une plateforme pensée pour apprendre à ton rythme, pratiquer avec intelligence et voir tes progrès prendre forme.</p></div><div class="auth-feature-grid"><div class="auth-feature"><div class="feature-icon">01</div><b>Apprentissage</b><span>Leçons adaptées</span></div><div class="auth-feature"><div class="feature-icon green">02</div><b>Missions</b><span>Situations utiles</span></div><div class="auth-feature"><div class="feature-icon amber">03</div><b>Prononciation</b><span>Travail de l'oral</span></div><div class="auth-feature"><div class="feature-icon red">04</div><b>Quiz</b><span>Défis rapides</span></div></div></div><div class="auth-panel"><div class="auth-panel-top"><div><div class="auth-welcome">Bienvenue !</div><div class="auth-welcome-sub">Ton espace d'apprentissage t'attend.</div></div><div class="secure-pill"><span class="secure-dot"></span> Connexion sécurisée</div></div></div></div>''', unsafe_allow_html=True)
    if not supabase_ready(): st.error("Configuration Supabase incomplète. Vérifie les Secrets Streamlit."); st.stop()
    col_left, col_right = st.columns([1.15, 1], gap="large")
    with col_left:
        st.markdown('<div class="auth-form-title">Ton espace personnel</div><div class="auth-form-subtitle">Connecte-toi avec ton e-mail et ton mot de passe.</div>', unsafe_allow_html=True)
        tabs = st.tabs(["Connexion", "Créer un compte"])
        with tabs[0]:
            with st.form("login_form"):
                email_input = st.text_input("E-mail", autocomplete="email", placeholder="exemple@email.com")
                password_input = st.text_input("Mot de passe", type="password", autocomplete="current-password")
                submitted = st.form_submit_button("Se connecter", use_container_width=True)
            if submitted:
                try:
                    with st.spinner("Ouverture de ton espace..."): sign_in(email_input or "", password_input or "")
                    st.rerun()
                except Exception as exc: st.error(str(exc))
        with tabs[1]:
            with st.form("registration_form"):
                email_input = st.text_input("E-mail", autocomplete="email", placeholder="exemple@email.com")
                pseudo_input = st.text_input("Pseudo (facultatif)", autocomplete="username", placeholder="Visible uniquement dans ton profil privé")
                password_input = st.text_input("Mot de passe", type="password", autocomplete="new-password")
                confirm_input = st.text_input("Confirmer le mot de passe", type="password", autocomplete="new-password")
                level_input = st.radio("Ton niveau d'études", LEVELS, horizontal=True)
                submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
            if submitted:
                try:
                    with st.spinner("Création de ton espace..."): message = sign_up(email_input or "", password_input or "", confirm_input or "", pseudo_input or "", level_input)
                    if st.session_state.get("identified"): st.rerun()
                    st.success(message)
                except Exception as exc: st.error(str(exc))
    with col_right:
        st.markdown('<div class="auth-side-card"><div class="side-card-icon">+</div><div class="side-card-title">Ton parcours reste privé.</div><p>Ton adresse e-mail et ton pseudo ne sont jamais affichés sur les pages publiques de FRANTSAY.</p><div class="side-check"><span>✓</span> Authentification Supabase</div><div class="side-check"><span>✓</span> Session restaurée après F5</div><div class="side-check"><span>✓</span> Niveau choisi une seule fois</div></div>', unsafe_allow_html=True)
    st.stop()


if not st.session_state.identified: render_auth_screen()


# =============================================================================
# 5bis. CONFIGURATION DE LA SESSION
# =============================================================================

level = st.session_state.level

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
        '<div class="tip"><span class="tag tag-amber">⏳</span> '
        "Les administrateurs sont en train d'activer l'IA, patientez s'il vous plaît. "
        "En attendant, les fiches de l'onglet Accueil restent consultables sans IA.</div>",
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




def level_instruction(level: str) -> str:
    rules = {
        "Collège": "Utilise un vocabulaire simple, des phrases courtes et des explications concrètes adaptées à un collégien.",
        "Lycée": "Utilise un vocabulaire intermédiaire, explique les règles avec précision et propose des exemples adaptés au lycée.",
        "Université": "Utilise un vocabulaire plus riche, des nuances grammaticales et des explications structurées adaptées à l'université.",
    }
    return rules.get(level, rules["Lycée"])


def prompt_with_level(base: str) -> str:
    return base + "\n\nNIVEAU PÉDAGOGIQUE VERROUILLÉ : " + st.session_state.level + "\n" + level_instruction(st.session_state.level)

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
  .rec-start { background: __PURPLE__; color: #fff; box-shadow: 0 4px 12px rgba(37,99,235,.28); }
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

/* L'ÂME DE MADAGASCAR */
:root { --tanety:#B83A24; --ravinala:#1B4D3E; --lamba:#E69A2A; --raphia:#FBF8F3; }
.stApp { background:var(--raphia) !important; }
.stApp, .stApp * { --purple:var(--tanety); --green:var(--ravinala); --amber:var(--lamba); }
.block-container { max-width:1180px; background:transparent; }
div.stButton > button { background:var(--tanety) !important; box-shadow:0 4px 12px rgba(184,58,36,.24) !important; }
div.stButton > button:hover { background:#9f301d !important; }
.st-key-auth_hero { background:linear-gradient(135deg,var(--ravinala),#12362d 60%,var(--tanety)) !important; }
.auth-kicker,.eyebrow,.wave { color:var(--tanety) !important; }
.tag-solid { background:var(--tanety) !important; border-color:var(--tanety) !important; }
.tag-green,.badge-ok { background:rgba(27,77,62,.10) !important; color:var(--ravinala) !important; border-color:rgba(27,77,62,.25) !important; }
.tag-amber,.badge-warn { background:rgba(230,154,42,.12) !important; color:#8A5A0B !important; border-color:rgba(230,154,42,.35) !important; }
.card,.lesson,.tip,.mini,.dashboard-stat,.auth-side-card,.identity-note { border-color:#E7DED3 !important; }
.card,.lesson,.tip,.mini,.dashboard-stat { background:rgba(255,255,255,.72) !important; }
.lesson { border-left-color:var(--tanety) !important; border-radius:14px; position:relative; }
.lesson:before { content:"◆ ◇ ◆"; display:block; color:var(--lamba); font-size:.48rem; letter-spacing:4px; margin-bottom:.35rem; opacity:.9; }
.phrase-modele { background:linear-gradient(135deg,var(--ravinala),#153f33) !important; }
section[data-testid="stSidebar"] { background:var(--ravinala) !important; border-right:0 !important; }
section[data-testid="stSidebar"] * { color:#F7F4EC !important; }
section[data-testid="stSidebar"] .sidebar-section-label { color:#BFD0C8 !important; }
section[data-testid="stSidebar"] div.stButton > button { border-color:rgba(230,154,42,.35) !important; color:#F6D18A !important; }
@media (max-width:700px) { .block-container { padding-left:.7rem; padding-right:.7rem; } .dashboard-stat-grid { grid-template-columns:repeat(2,1fr); } }
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
# 9. BARRE LATÉRALE — navigation du tableau de bord
# =============================================================================

with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand">{ROBOT_SVG}<div><strong>FRANTSAY</strong><span>Ton parcours de français</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-profile"><div class="profile-avatar">' + safe_html((st.session_state.user_pseudo or "F")[:1].upper()) + '</div><div><b>Profil privé</b><span>' + safe_html(st.session_state.level) + '</span></div></div>', unsafe_allow_html=True)
    with st.expander("Profil privé", expanded=False):
        st.caption("Ces informations ne sont pas affichées sur l'accueil.")
        st.write(f"E-mail : {st.session_state.user_email}")
        if st.session_state.user_pseudo:
            st.write(f"Pseudo : {st.session_state.user_pseudo}")
        st.write(f"Niveau verrouillé : {st.session_state.level}")

    st.markdown('<div class="sidebar-section-label">TON ESPACE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item active"><span>⌂</span> Tableau de bord</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>▣</span> Grammaire</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>◉</span> Missions</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>◌</span> Prononciation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>◇</span> Quiz</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">RÉGLAGES</div>', unsafe_allow_html=True)
    THEME_OPTIONS = ["Clair", "Sombre"]
    current_idx = 1 if st.session_state.theme == "dark" else 0
    picked = st.radio("Thème", THEME_OPTIONS, index=current_idx, horizontal=True, label_visibility="collapsed", key="theme_radio")
    picked_theme = "dark" if picked == THEME_OPTIONS[1] else "light"
    if picked_theme != st.session_state.theme:
        st.session_state.theme = picked_theme
        st.rerun()

    st.markdown('<div class="sidebar-section-label">PARCOURS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>LOCK</span> Niveau verrouillé : ' + safe_html(st.session_state.level) + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-stats"><div><span>POINTS</span><b>' + str(st.session_state.score) + '</b></div><div><span>ACTIVITÉS</span><b>' + str(st.session_state.questions_done) + '</b></div></div>', unsafe_allow_html=True)

    if st.button("Se déconnecter", key="logout_button", use_container_width=True):
        logout_user()
        st.rerun()


# =============================================================================
# 10. EN-TÊTE — hero compact avec illustration robot IA (ligne flex, robot à
#     droite du badge de statut, stable sur mobile comme sur desktop)
# =============================================================================

status = (
    '<span class="badge badge-ok"><span class="dot"></span>Assistant IA actif</span>'
    if api_available()
    else '<span class="badge badge-warn">Cours disponibles · IA non activée</span>'
)

with st.container(key="hero_box"):
    st.markdown(
        f"""<div class="dashboard-topline"><div><div class="eyebrow"><span class="tag tag-solid">FRANTSAY</span> TABLEAU DE BORD</div>
<h1 class="hero-title">Ton espace d'apprentissage <span class="wave">✦</span></h1>
<p class="hero-sub">Prêt à continuer ton apprentissage ? · Parcours {safe_html(level)}</p></div><div class="hero-user-badge"><span class="hero-avatar">FR</span><div><b>Profil privé</b><span>Niveau verrouillé</span></div></div></div>
<div class="dashboard-stat-grid"><div class="dashboard-stat"><span>PROGRESSION</span><b>{min(100, max(0, st.session_state.score))}%</b><small>Continue comme ça</small></div><div class="dashboard-stat"><span>POINTS</span><b>{st.session_state.score:,}</b><small>Points gagnés</small></div><div class="dashboard-stat"><span>ACTIVITÉS</span><b>{st.session_state.questions_done}</b><small>Défis réalisés</small></div><div class="dashboard-stat accent"><span>OBJECTIF</span><b>En route</b><small>Ton parcours avance</small></div></div>""",
        unsafe_allow_html=True,
    )

components.html(ROBOT_CLICK_JS, height=0)


# =============================================================================
# 11. ONGLETS ET MODULES
# =============================================================================

tab_home, tab_defis, tab_correction, tab_missions, tab_pron, tab_quiz = st.tabs(
    ["Accueil", "Défis", "Grammaire", "Missions", "Prononciation", "Quiz"]
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


# --- ONGLET : DÉFIS (parcours de paliers façon jeu vidéo) ---
with tab_defis:
    score = st.session_state.score
    st.markdown(
        '<div class="card"><span class="eyebrow">Progression</span>'
        "<h3 style=\"margin:.2rem 0;font-size:1rem\">Ton parcours de défis</h3>"
        f"<p style=\"margin:0;font-size:.8rem;color:var(--muted)\">Gagne des points en grammaire, "
        f"missions, prononciation et quiz pour débloquer chaque palier. Score actuel : <b>{score}</b> pts.</p></div>",
        unsafe_allow_html=True,
    )

    cards = []
    for i, (seuil, titre, desc) in enumerate(PALIERS):
        next_seuil = PALIERS[i + 1][0] if i + 1 < len(PALIERS) else None
        unlocked = score >= seuil
        completed = unlocked and next_seuil is not None and score >= next_seuil
        if completed:
            tag_html = '<span class="tag tag-green">TERMINÉ</span>'
        elif unlocked:
            tag_html = '<span class="tag tag-solid">EN COURS</span>'
        else:
            tag_html = '<span class="tag tag-muted">VERROUILLÉ</span>'

        progress_html = ""
        if unlocked and not completed and next_seuil is not None:
            pct = max(0, min(100, round((score - seuil) / (next_seuil - seuil) * 100)))
            progress_html = (
                f'<div style="margin-top:.5rem;height:6px;border-radius:99px;background:var(--tabs-bg);overflow:hidden">'
                f'<div style="height:100%;width:{pct}%;background:var(--purple);border-radius:99px"></div></div>'
            )

        cards.append(
            f'<div class="lesson" style="{"" if unlocked else "opacity:.55"}">'
            f'<span class="eyebrow">{tag_html}</span>'
            f"<b>{safe_html(titre)}</b>"
            f"<p>{safe_html(desc)}</p>"
            f"{progress_html}"
            "</div>"
        )
    st.markdown("".join(cards), unsafe_allow_html=True)


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
                save_current_progress()
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
        '<div class="card"><span class="eyebrow"><span class="tag tag-green">02</span>Missions</span>'
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
                save_current_progress()
            except Exception as exc:
                st.error(f"Erreur : {exc}")

    if st.session_state.last_dialogue:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(st.session_state.last_dialogue)
        st.markdown("</div>", unsafe_allow_html=True)


# --- ONGLET 03 : PRONONCIATION INTERACTIVE ---
with tab_pron:
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag tag-amber">03</span>Prononciation interactive</span>'
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
        "L'analyse démarre automatiquement.</p></div>",
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
                        save_current_progress()
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
        '<div class="card"><span class="eyebrow"><span class="tag tag-red">04</span>Révision</span>'
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
                save_current_progress()

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
