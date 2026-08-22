# -*- coding: utf-8 -*-
"""
FRANTSAY  — "L'AME DE MADAGASCAR" 
Plateforme d'apprentissage du francais pour eleves et etudiants a Madagascar.
Stack: Streamlit + Supabase Auth (Email/MDP) + Gemini + gTTS

"""

import base64
import io
import json
import os
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
from cryptography.fernet import Fernet, InvalidToken

# =============================================================================
# NOUVEAU : audio_recorder_streamlit pour capture audio robuste
# =============================================================================
try:
    from streamlit_mic_recorder import mic_recorder
    MIC_RECORDER_AVAILABLE = True
except ImportError:
    MIC_RECORDER_AVAILABLE = False

# =============================================================================
# NOUVEAU : extra_streamlit_components.CookieManager pour session persistante
# =============================================================================
try:
    import extra_streamlit_components as stx
    COOKIE_MANAGER_AVAILABLE = True
except ImportError:
    COOKIE_MANAGER_AVAILABLE = False


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

APP_NAME = "FRANTSAY"
MODEL_NAME = "gemini-3.6-flash"
SESSION_COOKIE_NAME = "frantsay_sid"
SESSION_MAX_AGE = 60 * 60 * 24 * 30
LEVELS = ["College", "Lycee", "Universite"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le francais",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# 2. PALETTE "L'AME DE MADAGASCAR" — Variables CSS avec support dark/light
# =============================================================================

THEME = {
    "bg": "#FBF8F3",
    "card": "#FFFFFF",
    "ink": "#1A1410",
    "muted": "#7A6E64",
    "line": "#E7DED3",
    "tanety": "#B83A24",
    "ravinala": "#1B4D3E",
    "lamba": "#E69A2A",
    "terre_foncee": "#8B2E1A",
    "ravinala_fonce": "#12362D",
    "lamba_fonce": "#B87A1A",
    "sable": "#FBF8F3",
    "sable_chaud": "#F5EDE3",
    "terre_clair": "#F3E5E0",
    "ravinala_clair": "#E8F0EC",
    "lamba_clair": "#FDF5E6",
    "terre_pale": "#FEF2F0",
    "shadow_rgb": "26,20,16",
    "scheme": "light",
}

ROOT_VARS = f"""
:root {{
    --bg: {THEME['bg']};
    --card: {THEME['card']};
    --ink: {THEME['ink']};
    --muted: {THEME['muted']};
    --line: {THEME['line']};
    --tanety: {THEME['tanety']};
    --ravinala: {THEME['ravinala']};
    --lamba: {THEME['lamba']};
    --terre-foncee: {THEME['terre_foncee']};
    --ravinala-fonce: {THEME['ravinala_fonce']};
    --lamba-fonce: {THEME['lamba_fonce']};
    --sable: {THEME['sable']};
    --sable-chaud: {THEME['sable_chaud']};
    --terre-clair: {THEME['terre_clair']};
    --ravinala-clair: {THEME['ravinala_clair']};
    --lamba-clair: {THEME['lamba_clair']};
    --terre-pale: {THEME['terre_pale']};
    --shadow-rgb: {THEME['shadow_rgb']};
    --radius: 18px;
    --radius-sm: 12px;
    --footer-h: 46px;
    color-scheme: {THEME['scheme']};

    /* Sidebar : palette sombre fixe, independante du theme clair/sombre de l'app */
    --sidebar-bg: #14171B;
    --sidebar-bg-alt: #1C2024;
    --sidebar-active-bg: #23272C;
    --sidebar-text: #E7E7E7;
    --sidebar-muted: #8A8F98;
    --sidebar-border: rgba(255,255,255,.08);
    --sidebar-accent: {THEME['lamba']};
}}

@media (prefers-color-scheme: dark) {{
    :root {{
        --bg: #1A1410;
        --card: #2A2018;
        --ink: #F5EDE3;
        --muted: #A89E94;
        --line: #3D3028;
        --tanety: #D45A3A;
        --ravinala: #2A7A62;
        --lamba: #F0B84A;
        --terre-foncee: #A04020;
        --ravinala-fonce: #1A5A48;
        --lamba-fonce: #C0902A;
        --sable: #1A1410;
        --sable-chaud: #2A2018;
        --terre-clair: #3D2820;
        --ravinala-clair: #1A3A30;
        --lamba-clair: #3D3020;
        --terre-pale: #3D2018;
        --shadow-rgb: 0,0,0;
    }}
}}
"""

# =============================================================================
# 2bis. SURCHARGE MANUELLE DU THEME (clair/sombre/auto) — reutilise THEME
# =============================================================================

DARK_MODE_OVERRIDE_CSS = """
<style>
:root {
    --bg: #1A1410; --card: #2A2018; --ink: #F5EDE3; --muted: #A89E94; --line: #3D3028;
    --tanety: #D45A3A; --ravinala: #2A7A62; --lamba: #F0B84A;
    --terre-foncee: #A04020; --ravinala-fonce: #1A5A48; --lamba-fonce: #C0902A;
    --sable: #1A1410; --sable-chaud: #2A2018;
    --terre-clair: #3D2820; --ravinala-clair: #1A3A30; --lamba-clair: #3D3020; --terre-pale: #3D2018;
    --shadow-rgb: 0,0,0;
    color-scheme: dark;
}
/* Ces surfaces utilisent un blanc fige dans le CSS d'origine : sans cette
   surcharge, le texte (clair en mode sombre) devient illisible dessus. */
.card, .lesson, .tip, .mini, .st-key-hero_box,
.identity-note, .hero-user-badge, .dashboard-stat, .auth-side-card {
    background: var(--card) !important;
}
.dashboard-stat.accent {
    background: linear-gradient(135deg, var(--tanety), var(--terre-foncee)) !important;
}
</style>
"""

LIGHT_MODE_OVERRIDE_CSS = f"""
<style>
:root {{
    --bg: {THEME['bg']}; --card: {THEME['card']}; --ink: {THEME['ink']};
    --muted: {THEME['muted']}; --line: {THEME['line']};
    --tanety: {THEME['tanety']}; --ravinala: {THEME['ravinala']}; --lamba: {THEME['lamba']};
    --terre-foncee: {THEME['terre_foncee']}; --ravinala-fonce: {THEME['ravinala_fonce']}; --lamba-fonce: {THEME['lamba_fonce']};
    --sable: {THEME['sable']}; --sable-chaud: {THEME['sable_chaud']};
    --terre-clair: {THEME['terre_clair']}; --ravinala-clair: {THEME['ravinala_clair']};
    --lamba-clair: {THEME['lamba_clair']}; --terre-pale: {THEME['terre_pale']};
    --shadow-rgb: {THEME['shadow_rgb']};
    color-scheme: light;
}}
</style>
"""


def apply_theme_preference() -> None:
    """Force clair/sombre si choisi manuellement dans les Parametres.
    En mode 'auto' (par defaut), aucune surcharge n'est injectee : le
    comportement existant (media prefers-color-scheme) reste inchange."""
    mode = st.session_state.get("theme_mode", "auto")
    if mode == "dark":
        st.markdown(DARK_MODE_OVERRIDE_CSS, unsafe_allow_html=True)
    elif mode == "light":
        st.markdown(LIGHT_MODE_OVERRIDE_CSS, unsafe_allow_html=True)


# =============================================================================
# 3. SVG MASCOTTE LEMURIEN
# =============================================================================

LEMUR_SVG = """<svg class="hero-lemur-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mascotte lemurien FRANTSAY" tabindex="0">
<defs>
<linearGradient id="lemurBodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="var(--tanety)" />
<stop offset="100%" stop-color="var(--terre-foncee)" />
</linearGradient>
<linearGradient id="lemurStripeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
<stop offset="0%" stop-color="var(--ravinala)" />
<stop offset="100%" stop-color="var(--ravinala-fonce)" />
</linearGradient>
</defs>
<path d="M 95 85 Q 115 75 110 55 Q 105 35 90 45 Q 80 52 85 62" stroke="var(--tanety)" stroke-width="4" fill="none" stroke-linecap="round"/>
<ellipse cx="60" cy="72" rx="32" ry="28" fill="url(#lemurBodyGrad)" />
<rect x="35" y="58" width="50" height="4" rx="2" fill="url(#lemurStripeGrad)" opacity="0.6"/>
<rect x="38" y="68" width="44" height="4" rx="2" fill="url(#lemurStripeGrad)" opacity="0.6"/>
<rect x="42" y="78" width="36" height="4" rx="2" fill="url(#lemurStripeGrad)" opacity="0.6"/>
<circle cx="60" cy="38" r="22" fill="var(--card)" stroke="var(--line)" stroke-width="1.5"/>
<ellipse cx="60" cy="40" rx="14" ry="12" fill="var(--sable-chaud)" />
<circle class="lemur-eye" cx="52" cy="36" r="5.5" fill="var(--ravinala)" />
<circle class="lemur-eye" cx="68" cy="36" r="5.5" fill="var(--ravinala)" />
<circle cx="53" cy="34.5" r="1.8" fill="#FFFFFF" opacity=".9" />
<circle cx="69" cy="34.5" r="1.8" fill="#FFFFFF" opacity=".9" />
<ellipse cx="60" cy="46" rx="5" ry="3.5" fill="var(--tanety)" opacity=".7"/>
<ellipse cx="38" cy="28" rx="6" ry="8" fill="var(--card)" stroke="var(--line)" stroke-width="1" transform="rotate(-20 38 28)"/>
<ellipse cx="82" cy="28" rx="6" ry="8" fill="var(--card)" stroke="var(--line)" stroke-width="1" transform="rotate(20 82 28)"/>
<path d="M 54 50 Q 60 55 66 50" stroke="var(--tanety)" stroke-width="2" stroke-linecap="round" fill="none" opacity=".7"/>
<ellipse cx="42" cy="95" rx="7" ry="5" fill="var(--card)" stroke="var(--line)" stroke-width="1"/>
<ellipse cx="78" cy="95" rx="7" ry="5" fill="var(--card)" stroke="var(--line)" stroke-width="1"/>
</svg>"""

# =============================================================================
# 3bis. LOGO FRANTSAY — Maki + Soundwave F (remplace l'ancien logo rond orange)
# =============================================================================

FRANTSAY_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="48" height="48" style="vertical-align: middle; margin-right: 6px;">
  <rect width="200" height="200" rx="40" fill="#0A0E19"/>
  <!-- Tronc du baobab : axe vertical du F -->
  <path d="M 66 40 L 94 40 L 94 170 L 66 170 Z" fill="#F8FAFC"/>
  <!-- Racines evasees a la base du tronc -->
  <path d="M 66 170 L 40 192 L 66 182 Z" fill="#F8FAFC"/>
  <path d="M 94 170 L 120 192 L 94 182 Z" fill="#F8FAFC"/>
  <!-- Ramures superieures du baobab, de part et d'autre du tronc -->
  <path d="M 70 40 L 58 14 L 78 28 Z" fill="#F8FAFC"/>
  <path d="M 90 40 L 102 14 L 82 28 Z" fill="#F8FAFC"/>
  <!-- Barre superieure du F : queue annelee du maki (Lemur catta), bandes alternees -->
  <path d="M 94 36 L 156 36 L 156 62 L 94 62 Z" fill="#F8FAFC"/>
  <path d="M 94 36 L 110 36 L 110 62 L 94 62 Z" fill="#0A0E19"/>
  <path d="M 126 36 L 142 36 L 142 62 L 126 62 Z" fill="#0A0E19"/>
  <!-- Extremite recourbee de la queue -->
  <path d="M 156 36 C 176 36, 184 18, 170 8 C 160 0, 146 8, 152 22 L 156 36 Z" fill="#F8FAFC"/>
  <path d="M 161 15 L 171 21" stroke="#0A0E19" stroke-width="6" stroke-linecap="round"/>
  <!-- Barre mediane du F : seconde bande annelee, plus courte -->
  <path d="M 94 90 L 140 90 L 140 112 L 94 112 Z" fill="#F8FAFC"/>
  <path d="M 94 90 L 106 90 L 106 112 L 94 112 Z" fill="#0A0E19"/>
  <path d="M 118 90 L 130 90 L 130 112 L 118 112 Z" fill="#0A0E19"/>
</svg>"""

LEMUR_CLICK_JS = """
<script>
(function() {
    var win = window.parent || window;
    var doc = win.document;
    var attemptsLeft = 20;
    function bindLemur() {
        var el = doc.querySelector('.hero-lemur-svg');
        if (!el) { attemptsLeft -= 1; if (attemptsLeft > 0) setTimeout(bindLemur, 150); return; }
        if (el.dataset.frantsayBound === "1") return;
        el.dataset.frantsayBound = "1";
        function bounce() {
            el.classList.remove('lemur-clicked');
            void el.offsetWidth;
            el.classList.add('lemur-clicked');
        }
        el.addEventListener('click', bounce);
        el.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); bounce(); }
        });
        el.addEventListener('animationend', function(e) {
            if (e.animationName === 'lemurClickBounce') el.classList.remove('lemur-clicked');
        });
    }
    bindLemur();
})();
</script>
"""


# =============================================================================
# 4. CSS COMPLET — "L'AME DE MADAGASCAR" avec fond Baobabs immersif
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600&display=swap');
""" + ROOT_VARS + """

html, body, [class*="css"] { font-family: "Plus Jakarta Sans", "Inter", sans-serif; }
html { scroll-behavior: smooth; }
* { -webkit-tap-highlight-color: transparent; }

/* === SURFACE DE L'APPLICATION === */
.stApp {
    background: var(--bg);
    color: var(--ink);
    transition: background-color .25s ease, color .25s ease;
}


h1, h2, h3, h4, h5, p, label { color: var(--ink); }
.stApp .stMarkdown, .stApp .stText, .stApp [data-testid="stCaptionContainer"] { color: var(--ink); }
.auth-shell, .auth-shell p, .auth-shell label, .auth-shell .auth-form-title, .auth-shell .auth-form-subtitle { color: #F8FAF9; }


.block-container {
    max-width: 700px;
    padding-top: 1.3rem;
    padding-bottom: calc(var(--footer-h) + 1.4rem);
    padding-left: .9rem;
    padding-right: .9rem;
    transition: max-width .2s ease;
    position: relative;
    z-index: 1;
}

@media (min-width: 768px) {
    .block-container { max-width: 760px; padding-top: 1.8rem; }
    .card, .lesson { padding: 1rem 1.15rem; }
}
@media (min-width: 1100px) {
    .block-container { max-width: 820px; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}

.card, .lesson, .tip, .mini, .st-key-hero_box {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: 0 4px 14px -6px rgba(var(--shadow-rgb), 0.12);
    transition: transform .2s cubic-bezier(.16,1,.3,1), box-shadow .2s cubic-bezier(.16,1,.3,1),
                background-color .25s ease, border-color .25s ease;
    will-change: transform;
    backdrop-filter: blur(8px);
}

@media (hover: hover) and (pointer: fine) {
    .card:hover, .lesson:hover { transform: translateY(-2px); box-shadow: 0 12px 26px -10px rgba(var(--shadow-rgb),.18); border-color: var(--tanety); }
}
.card:active, .lesson:active { transform: scale(.985); }

.st-key-hero_box {
    padding: 1rem 1.1rem;
    margin-bottom: .7rem;
    background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(250,246,240,0.98) 100%);
    overflow: hidden;
    position: relative;
}
.st-key-hero_box [data-testid="stVerticalBlockBorderWrapper"] { background: transparent; border: 0; }

.aloalo-divider {
    display: flex;
    align-items: center;
    gap: .5rem;
    margin: 1rem 0;
    color: var(--lamba);
    font-size: .65rem;
    letter-spacing: 3px;
    opacity: .5;
}
.aloalo-divider::before, .aloalo-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--line), transparent);
}
.aloalo-divider span { color: var(--lamba); font-weight: 800; }

.hero-title {
    font-size: clamp(1.1rem, 4.2vw, 1.5rem);
    font-weight: 800;
    letter-spacing: -.5px;
    margin: .3rem 0 .2rem 0;
    line-height: 1.15;
}
.hero-sub { margin: 0; font-size: .8rem; color: var(--muted); }

.hero-status-row {
    margin-top: .5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: .6rem;
}

.st-key-auth_hero {
    background: linear-gradient(135deg, var(--ravinala) 0%, var(--ravinala-fonce) 55%, var(--tanety) 100%);
    border: none;
    border-radius: var(--radius);
    padding: 1.3rem 1.2rem;
    margin-bottom: .7rem;
    box-shadow: 0 14px 30px -12px rgba(27,77,62,.45);
    overflow: hidden;
    position: relative;
}
.st-key-auth_hero::after {
    content: "";
    position: absolute;
    width: 320px; height: 320px;
    right: -100px; bottom: -180px;
    border: 1px solid rgba(230,154,42,.15);
    border-radius: 50%;
    box-shadow: 0 0 0 30px rgba(230,154,42,.03), 0 0 0 60px rgba(230,154,42,.02);
}
.st-key-auth_hero [data-testid="stVerticalBlockBorderWrapper"] { background: transparent; border: 0; }

.auth-shell { display: grid; grid-template-columns: 1.25fr .85fr; gap: 2rem; position: relative; z-index: 1; }
.auth-copy { color: #fff; min-height: 360px; display: flex; flex-direction: column; justify-content: space-between; }

.brand-lockup { display: flex; align-items: center; gap: .7rem; }
.brand-lockup .hero-lemur-svg { width: 52px; }
.brand-name { color: #fff; font-size: 1.55rem; font-weight: 800; letter-spacing: -.8px; }
.brand-kicker { color: rgba(255,255,255,.48); font-size: .56rem; letter-spacing: 1.5px; font-weight: 700; margin-top: .12rem; }

.auth-copy-body { padding: 1.7rem 0 1rem; max-width: 610px; }
.auth-kicker { color: var(--lamba); font-size: .7rem; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: .55rem; }
.auth-main-title { color: #fff !important; font-size: clamp(2.15rem, 5vw, 3.45rem); line-height: 1.02; letter-spacing: -1.8px; margin: 0; font-weight: 800; }
.auth-main-title span { background: linear-gradient(90deg, var(--lamba), #F0C674); -webkit-background-clip: text; background-clip: text; color: transparent !important; }
.auth-main-sub { color: rgba(255,255,255,.68) !important; font-size: .94rem; line-height: 1.65; max-width: 560px; margin: .9rem 0 0; }

.auth-feature-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: .55rem; max-width: 680px; }
.auth-feature {
    border: 1px solid rgba(255,255,255,.13);
    background: rgba(255,255,255,.055);
    border-radius: 16px;
    padding: .8rem .72rem;
    backdrop-filter: blur(8px);
}
.auth-feature b, .auth-feature span { display: block; color: #fff; }
.auth-feature b { font-size: .72rem; margin-top: .55rem; }
.auth-feature span { color: rgba(255,255,255,.48); font-size: .58rem; margin-top: .14rem; }

.feature-icon {
    width: 27px; height: 27px; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(184,58,36,.14); color: #F4A896;
    font: 700 .58rem "JetBrains Mono";
    border: 1px solid rgba(184,58,36,.25);
}
.feature-icon.green { color: #8FD9C4; background: rgba(27,77,62,.14); border-color: rgba(27,77,62,.25); }
.feature-icon.amber { color: #F5D89A; background: rgba(230,154,42,.12); border-color: rgba(230,154,42,.22); }
.feature-icon.red { color: #F4A896; background: rgba(184,58,36,.14); border-color: rgba(184,58,36,.25); }

.auth-panel {
    min-height: 360px;
    border-radius: 22px;
    border: 1px solid rgba(255,255,255,.12);
    background: linear-gradient(145deg, rgba(255,255,255,.075), rgba(255,255,255,.035));
    box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
    padding: 1.4rem;
    display: flex;
    align-items: flex-end;
}
.auth-panel-top { width: 100%; display: flex; align-items: flex-start; justify-content: space-between; gap: .8rem; }
.auth-welcome { color: #fff; font-size: 1.15rem; font-weight: 800; }
.auth-welcome-sub { color: rgba(255,255,255,.55); font-size: .72rem; margin-top: .2rem; }
.secure-pill { color: #A7F3D0; border: 1px solid rgba(52,211,153,.22); background: rgba(52,211,153,.08); padding: .35rem .55rem; border-radius: 999px; font-size: .58rem; white-space: nowrap; }
.secure-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #34D399; box-shadow: 0 0 8px #34D399; }

.hero-lemur-svg {
    width: clamp(38px, 11vw, 52px);
    flex: none;
    display: block;
    cursor: pointer;
    filter: drop-shadow(0 6px 14px rgba(var(--shadow-rgb), .2));
    animation: lemurFloat 3.6s ease-in-out infinite;
}
.hero-lemur-svg.lemur-clicked { animation: lemurClickBounce .6s cubic-bezier(.34,1.56,.64,1); }
@keyframes lemurClickBounce {
    0% { transform: scale(1) rotate(0deg); }
    30% { transform: scale(1.18) rotate(-10deg); }
    55% { transform: scale(.93) rotate(8deg); }
    80% { transform: scale(1.05) rotate(-3deg); }
    100% { transform: scale(1) rotate(0deg); }
}
@keyframes lemurFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
}
.lemur-eye {
    filter: drop-shadow(0 0 5px var(--ravinala));
    animation: lemurEyeGlow 2.4s ease-in-out infinite;
}
@keyframes lemurEyeGlow {
    0%, 100% { opacity: 1; }
    50% { opacity: .6; }
}

.auth-form-title { font-size: 1.25rem; font-weight: 800; letter-spacing: -.5px; margin-bottom: .2rem; }
 .auth-form-subtitle { color: rgba(255,255,255,.78) !important; font-size: .78rem; margin-bottom: .8rem; }
.auth-shell [data-testid="stForm"],
.auth-shell [data-testid="stTabs"] {
    color: #F8FAF9;
}
.auth-shell [data-testid="stWidgetLabel"] p,
.auth-shell [data-testid="stWidgetLabel"] label,
.auth-shell .stRadio label,
.auth-shell [data-baseweb="tab"] {
    color: #F8FAF9 !important;
}
.auth-shell [data-testid="stTextInput"] input {
    color: #1A1410 !important;
    background: #FFFFFF !important;
    border: 1px solid #D8D0C7 !important;
}
.auth-shell [data-testid="stTextInput"] input::placeholder { color: #7A6E64 !important; }
.auth-shell [data-testid="stFormSubmitButton"] button {
    background: #B83A24 !important;
    color: #FFFFFF !important;
    border: 0 !important;
    font-weight: 800 !important;
}
.auth-shell [data-baseweb="tab-highlight"] { background-color: #E69A2A !important; }
.auth-side-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.95), var(--terre-clair));
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1.35rem;
    box-shadow: 0 18px 45px rgba(var(--shadow-rgb), .12);
    margin-top: 1.4rem;
}
.side-card-icon {
    width: 40px; height: 40px; border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, var(--tanety), var(--terre-foncee));
    color: #fff; font-size: 1.1rem;
    box-shadow: 0 10px 22px rgba(184,58,36,.25);
}
.side-card-title { font-weight: 800; font-size: 1.02rem; margin-top: .8rem; }
.auth-side-card p { color: var(--muted); font-size: .76rem; line-height: 1.55; }
.side-check { display: flex; align-items: center; gap: .5rem; font-size: .7rem; font-weight: 700; margin-top: .6rem; }
.side-check span { width: 20px; height: 20px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: var(--ravinala-clair); color: var(--ravinala); border: 1px solid rgba(27,77,62,.2); }

.auth-trust-line {
    margin-top: 1.4rem;
    padding: .95rem 1rem;
    border-radius: 16px;
    background: rgba(255,255,255,.92);
    border: 1px solid rgba(255,255,255,.72);
    box-shadow: 0 12px 30px rgba(0,0,0,.12);
    color: #17352C !important;
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: .55rem;
    align-items: center;
}
.auth-trust-line span { grid-row: span 2; color: #1B6B52 !important; font-size: 1.15rem; }
.auth-trust-line b { color: #17352C !important; font-size: .78rem; }
.auth-trust-line small { color: #5F6B66 !important; font-size: .68rem; }
.identity-note {
    display: flex; gap: .7rem; align-items: center;
    padding: .85rem .95rem; margin-top: .7rem;
    border: 1px solid var(--line); background: rgba(255,255,255,0.96);
    border-radius: 17px;
}
.identity-note-icon {
    width: 34px; height: 34px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    background: var(--terre-clair); color: var(--tanety); font-size: 1rem;
    flex-shrink: 0;
}
.identity-note-text {
    display: flex;
    flex-direction: column;
    gap: .2rem;
}
.identity-note-text b { font-size: .74rem; color: var(--ink); }
.identity-note-text span { color: var(--muted); font-size: .68rem; line-height: 1.5; }

.st-key-hero_box { background: transparent; border: 0; padding: 0; }
.dashboard-topline { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .3rem 0 1rem; }
.dashboard-topline .hero-title { margin: .25rem 0 .15rem; }
.wave { color: var(--tanety); }

.hero-user-badge {
    display: flex; align-items: center; gap: .65rem;
    padding: .55rem .7rem; border: 1px solid var(--line);
    background: rgba(255,255,255,0.96); border-radius: 16px;
}
.hero-avatar {
    width: 36px; height: 36px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, var(--tanety), var(--terre-foncee));
    color: #fff; font-weight: 800;
}
.hero-user-badge b, .hero-user-badge span { display: block; }
.hero-user-badge b { font-size: .7rem; }
.hero-user-badge span { color: var(--muted); font-size: .58rem; max-width: 170px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.dashboard-stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: .7rem; margin: .4rem 0 1rem; }
.dashboard-stat {
    background: rgba(255,255,255,0.96); border: 1px solid var(--line);
    border-radius: 18px; padding: 1rem;
    box-shadow: 0 10px 25px rgba(var(--shadow-rgb), .065);
    backdrop-filter: blur(8px);
}
.dashboard-stat.accent {
    background: linear-gradient(135deg, var(--tanety), var(--terre_foncee));
    border-color: transparent;
}
.dashboard-stat span, .dashboard-stat small { display: block; }
.dashboard-stat span { color: var(--muted); font: 700 .55rem "JetBrains Mono"; letter-spacing: .7px; }
.dashboard-stat b { display: block; font-size: 1.25rem; letter-spacing: -.5px; margin: .28rem 0 .1rem; }
.dashboard-stat small { color: var(--muted); font-size: .58rem; }
.dashboard-stat.accent span, .dashboard-stat.accent b, .dashboard-stat.accent small { color: #fff; }

.card { padding: .85rem .95rem; margin-bottom: .6rem; }
.mini { padding: .65rem .75rem; }

.eyebrow {
    color: var(--tanety);
    font-size: .66rem;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: .35rem;
}

.tag {
    display: inline-flex; align-items: center; justify-content: center;
    font-family: "JetBrains Mono", monospace;
    font-size: .62rem; font-weight: 700; letter-spacing: .3px;
    padding: .12rem .38rem;
    border-radius: 6px;
    background: var(--terre-clair);
    color: var(--tanety);
    border: 1px solid rgba(184,58,36,.15);
}
.tag-solid { background: var(--tanety); color: #fff; border-color: var(--tanety); }
.tag-green { background: var(--ravinala-clair); color: var(--ravinala); border-color: rgba(27,77,62,.2); }
.tag-red { background: var(--terre-pale); color: var(--terre-foncee); border-color: rgba(184,58,36,.2); }
.tag-amber { background: var(--lamba-clair); color: var(--lamba-fonce); border-color: rgba(230,154,42,.3); }
.tag-muted { background: var(--sable-chaud); color: var(--muted); border-color: var(--line); }

.badge {
    display: inline-flex; align-items: center; gap: .4rem;
    padding: .3rem .65rem; border-radius: 999px;
    font-size: .68rem; font-weight: 700;
}
.badge-ok { background: var(--ravinala-clair); color: var(--ravinala); border: 1px solid rgba(27,77,62,.2); }
.badge-warn { background: var(--lamba-clair); color: var(--lamba-fonce); border: 1px solid rgba(230,154,42,.3); }

.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--ravinala); box-shadow: 0 0 6px var(--ravinala); }

.grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: .5rem;
    margin-bottom: .6rem;
}

.lesson {
    padding: .7rem .75rem;
    border-left: 3px solid var(--tanety);
    border-radius: var(--radius-sm);
    position: relative;
}
.lesson b { font-size: .82rem; }
.lesson p { font-size: .76rem; margin: .25rem 0; color: var(--muted); }

.lesson::before {
    content: "<> <> <>";
    display: block;
    color: var(--lamba);
    font-size: .48rem;
    letter-spacing: 4px;
    margin-bottom: .35rem;
    opacity: .9;
    font-family: "JetBrains Mono", monospace;
}

.grid-2 .lesson:nth-child(4n+2) { border-left-color: var(--ravinala); }
.grid-2 .lesson:nth-child(4n+3) { border-left-color: var(--lamba); }
.grid-2 .lesson:nth-child(4n+4) { border-left-color: var(--terre-foncee); }

.tip {
    background: var(--terre-clair);
    border-color: rgba(184,58,36,.12);
    padding: .7rem .8rem;
    font-size: .8rem;
}

.capsule {
    display: inline-flex; flex-direction: column;
    border-radius: 12px; padding: .4rem .6rem; margin: .15rem .25rem .15rem 0;
    border: 1px solid; min-width: 90px;
}
.capsule-type { font-size: .55rem; font-weight: 800; text-transform: uppercase; letter-spacing: .4px; }
.capsule-text { font-weight: 700; margin-top: .1rem; font-size: .82rem; }

.sujet { background: var(--sable-chaud); border-color: var(--line); color: var(--tanety); }
.verbe { background: var(--ravinala-clair); border-color: rgba(27,77,62,.2); color: var(--ravinala); }
.complement { background: var(--lamba-clair); border-color: rgba(230,154,42,.3); color: var(--lamba-fonce); }
.autre { background: var(--sable-chaud); border-color: var(--line); color: var(--muted); }

.phrase-modele {
    background: linear-gradient(135deg, var(--ravinala) 0%, var(--ravinala-fonce) 100%);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    color: white;
    margin-bottom: .6rem;
    box-shadow: 0 10px 24px -10px rgba(27,77,62,.5);
    position: relative;
    overflow: hidden;
}
.phrase-modele::after {
    content: "";
    position: absolute;
    top: -30px; right: -30px;
    width: 100px; height: 100px;
    border: 1px solid rgba(230,154,42,.15);
    border-radius: 50%;
    box-shadow: 0 0 0 20px rgba(230,154,42,.03);
}
.phrase-modele .eyebrow2 {
    font-size: .62rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
    color: rgba(255,255,255,.82); margin-bottom: .3rem; display: block;
}
.phrase-modele h3 { color: white !important; margin: 0; font-size: 1.05rem; line-height: 1.35; }

.faute {
    border: 1px solid rgba(230,154,42,.3);
    background: var(--lamba-clair);
    border-radius: 12px;
    padding: .55rem .7rem;
    margin-bottom: .4rem;
    font-size: .8rem;
}
.faute .mot { font-weight: 800; color: var(--lamba-fonce); }

div.stButton > button {
    border: 0 !important;
    border-radius: 12px !important;
    padding: .55rem 1.1rem !important;
    font-weight: 700 !important;
    font-size: .85rem !important;
    background: var(--tanety) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(184, 58, 36, 0.28) !important;
    transition: transform .18s cubic-bezier(.16,1,.3,1), box-shadow .18s ease, filter .18s ease !important;
    width: 100%;
}
@media (hover: hover) and (pointer: fine) {
    div.stButton > button:hover { transform: scale(1.015); box-shadow: 0 6px 16px rgba(184, 58, 36, 0.38) !important; filter: brightness(1.05); }
}
div.stButton > button:active { transform: scale(0.97); }
div.stButton > button:focus-visible { outline: 2px solid var(--tanety) !important; outline-offset: 2px; }

.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stFileUploader section {
    background: rgba(255,255,255,0.92) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    transition: border-color .18s ease, box-shadow .18s ease !important;
}
.stTextInput input:focus, .stTextArea textarea:focus,
.stSelectbox div[data-baseweb="select"]:focus-within > div {
    border-color: var(--tanety) !important;
    box-shadow: 0 0 0 3px var(--terre-clair) !important;
}

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
li[data-baseweb="option"] * { color: inherit !important; }
li[data-baseweb="option"]:hover,
li[data-baseweb="option"][aria-selected="true"] {
    background: var(--terre-clair) !important;
    color: var(--tanety) !important;
}

/* === SIDEBAR — sombre, minimaliste, sans emoji === */
section[data-testid="stSidebar"] {
    background: #14171B !important;
    border-right: 1px solid rgba(255,255,255,.08);
    min-width: 250px; max-width: 280px;
}
section[data-testid="stSidebar"] * { color: var(--sidebar-text) !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] > div:first-child {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    padding-bottom: 1rem;
}

.sidebar-logo {
    display: flex; align-items: center; gap: .6rem;
    padding: .2rem .1rem 1.1rem;
    margin-bottom: .4rem;
    border-bottom: 1px solid var(--sidebar-border);
}
.sidebar-logo-mark {
    width: 34px; height: 34px; flex: none;
    display: grid; place-items: center;
    border-radius: 10px;
    overflow: hidden;
}
.sidebar-logo-mark svg { width: 100%; height: 100%; display: block; }
.sidebar-logo-word {
    color: #fff !important; font-weight: 800;
    font-size: .92rem; letter-spacing: .06em;
}

/* Menu vertical construit sur st.sidebar.radio, dot masque */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    display: flex; flex-direction: column; gap: .1rem;
    margin-top: .2rem;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    display: flex; align-items: center;
    width: 100%; margin: 0 !important;
    padding: .6rem .65rem;
    border-radius: 10px;
    cursor: pointer;
    font-size: .8rem; font-weight: 600;
    color: var(--sidebar-muted) !important;
    background: transparent;
    transition: background .15s ease, color .15s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: var(--sidebar-bg-alt);
    color: var(--sidebar-text) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background: var(--sidebar-active-bg);
    color: #fff !important;
    box-shadow: inset 3px 0 0 var(--sidebar-accent);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none;
}

.sidebar-spacer { flex: 1 1 auto; }

.st-key-sidebar_logout { margin-top: auto; padding-top: 1rem; }
.st-key-sidebar_logout [data-testid="stVerticalBlockBorderWrapper"] { background: transparent; border: 0; }
section[data-testid="stSidebar"] div.stButton > button {
    background: transparent !important;
    border: 1px solid var(--sidebar-border) !important;
    color: var(--sidebar-muted) !important;
    box-shadow: none !important;
    font-weight: 600;
}
section[data-testid="stSidebar"] div.stButton > button:hover {
    border-color: var(--tanety) !important;
    color: #fff !important;
    background: rgba(184,58,36,.14) !important;
}

.app-footer {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    height: var(--footer-h);
    display: flex; align-items: center; justify-content: center;
    background: rgba(251,248,243,.92);
    backdrop-filter: blur(6px);
    border-top: 1px solid var(--line);
    color: var(--muted);
    font-size: .72rem;
    z-index: 999;
}
.app-footer b { color: var(--ink); font-weight: 700; }

@media (max-width: 850px) {
    .auth-shell { grid-template-columns: 1fr; }
    .auth-panel { min-height: 90px; }
    .auth-copy { min-height: 0; }
    .auth-feature-grid { grid-template-columns: repeat(2, 1fr); }
    .dashboard-stat-grid { grid-template-columns: repeat(2, 1fr); }
    .dashboard-topline { align-items: flex-start; }
}
@media (max-width: 560px) {
    .block-container { padding-left: .65rem; padding-right: .65rem; }
    .st-key-auth_hero { padding: 1.35rem 1rem; border-radius: 22px; }
    .auth-main-title { font-size: 2.15rem; }
    .auth-feature-grid { grid-template-columns: repeat(2, 1fr); }
    .auth-panel { display: none; }
    .dashboard-topline { display: block; }
    .hero-user-badge { margin-top: .7rem; width: max-content; }
    .dashboard-stat-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
    .grid-2 { gap: .4rem; }
}

/* === LOGO FRANTSAY + NAVIGATION UNIFIEE === */
.frantsay-logo {
    display: inline-flex;
    align-items: center;
    gap: .75rem;
    margin: .15rem 0 .9rem;
    padding: .55rem .8rem .55rem .55rem;
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 18px;
    background: rgba(255,255,255,.08);
    backdrop-filter: blur(12px);
    box-shadow: 0 12px 32px rgba(0,0,0,.16);
}
.frantsay-logo-mark {
    width: 42px; height: 42px;
    display: grid; place-items: center;
    border-radius: 13px;
    background: linear-gradient(135deg, var(--lamba), var(--tanety));
    color: #fff;
    font-weight: 900;
    letter-spacing: -.08em;
    box-shadow: 0 8px 20px rgba(184,58,36,.3);
}
.frantsay-logo-word {
    color: #fff;
    font-size: clamp(1.05rem, 4vw, 1.35rem);
    line-height: 1;
    font-weight: 900;
    letter-spacing: .08em;
}
.frantsay-logo-sub {
    color: rgba(255,255,255,.68);
    font-size: .52rem;
    letter-spacing: .14em;
    font-weight: 700;
    margin-top: .22rem;
}
body:not(.frantsay-welcome) .frantsay-logo {
    background: var(--card);
    border-color: var(--line);
    box-shadow: 0 8px 22px rgba(var(--shadow-rgb),.08);
}
body:not(.frantsay-welcome) .frantsay-logo-word { color: var(--ink); }
body:not(.frantsay-welcome) .frantsay-logo-sub { color: var(--muted); }


.auth-shell .stTextInput label,
.auth-shell [data-testid="stWidgetLabel"] p,
.auth-shell [data-testid="stWidgetLabel"] label {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
.auth-shell [data-testid="stForm"] {
    background: rgba(12, 30, 25, .76);
    border: 1px solid rgba(255,255,255,.14);
    border-radius: 18px;
    padding: 1rem;
    backdrop-filter: blur(10px);
}
@media (max-width: 650px) {
    .ton-espace-nav { padding: .7rem; border-radius: 16px; }
    [data-testid="stSegmentedControl"] > div {
        justify-content: flex-start;
        padding-bottom: .12rem;
    }
    [data-testid="stSegmentedControl"] button {
        min-width: 112px;
        font-size: .75rem !important;
    }
}
@media (max-width: 480px) {
    .frantsay-logo { width: 100%; box-sizing: border-box; }
    .frantsay-logo-mark { width: 38px; height: 38px; }
}
.palier-progress {
    margin-top: .5rem;
    height: 6px;
    border-radius: 99px;
    background: var(--sable-chaud);
    overflow: hidden;
}
.palier-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--tanety), var(--lamba));
    border-radius: 99px;
    transition: width .6s cubic-bezier(.16,1,.3,1);
}

.lamba-badge {
    display: inline-flex;
    align-items: center;
    gap: .3rem;
    padding: .25rem .55rem;
    border-radius: 999px;
    background: var(--lamba-clair);
    border: 1px solid rgba(230,154,42,.25);
    color: var(--lamba-fonce);
    font-size: .65rem;
    font-weight: 700;
}

.config-alert {
    display: flex;
    align-items: flex-start;
    gap: .9rem;
    background: linear-gradient(135deg, rgba(184,58,36,.10), rgba(184,58,36,.03));
    border: 1px solid rgba(184,58,36,.35);
    border-radius: 16px;
    padding: 1.1rem 1.3rem;
    margin: .5rem 0 1rem;
}
.config-alert-icon {
    flex-shrink: 0;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: var(--tanety);
    color: #fff;
    font-weight: 800;
    font-size: 1.05rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 6px 14px rgba(184,58,36,.35);
}
.config-alert-title {
    font-weight: 800;
    font-size: 1rem;
    color: var(--ink, #1B1B1B);
    margin-bottom: .2rem;
}
.config-alert-sub {
    font-size: .84rem;
    line-height: 1.5;
    color: rgba(27,27,27,.72);
}
.config-alert-sub code {
    background: rgba(27,27,27,.08);
    padding: .05rem .35rem;
    border-radius: 6px;
    font-size: .78rem;
}

/* Erreurs Streamlit : contraste lisible et sobre */
[data-testid="stAlert"] {
    border-radius: 14px !important;
    border: 1px solid rgba(184,58,36,.25) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {
    color: #5A1F18 !important;
}
[data-testid="stAlert"][data-baseweb="notification"] {
    background: #FFF3F0 !important;
}
.maintenance-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: .9rem;
    max-width: 460px;
    margin: 2.2rem auto;
    padding: 2.4rem 1.8rem;
    border-radius: 24px;
    background: linear-gradient(160deg, var(--ravinala) 0%, var(--ravinala-fonce) 100%);
    box-shadow: 0 22px 44px -18px rgba(var(--shadow-rgb),.45);
    position: relative;
    overflow: hidden;
}
.maintenance-screen::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 15% 20%, rgba(255,255,255,.07), transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(230,154,42,.15), transparent 45%);
    pointer-events: none;
}
.maintenance-badge {
    width: 62px;
    height: 62px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--tanety), var(--terre-foncee));
    box-shadow: 0 10px 24px -6px rgba(184,58,36,.55);
    z-index: 1;
}
.maintenance-title {
    color: #fff;
    font-weight: 800;
    font-size: 1.2rem;
    z-index: 1;
}
.maintenance-sub {
    color: rgba(255,255,255,.82);
    font-size: .88rem;
    line-height: 1.6;
    z-index: 1;
}

.ton-espace-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: .5rem 0 1rem;
}
.ton-espace-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--ink);
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #0D1815;
        --card: #16241F;
        --ink: #F3F7F5;
        --muted: #B8C5BF;
        --line: #33453E;
        --sable: #0D1815;
        --sable-chaud: #18241F;
    }
    .card, .lesson, .tip, .mini, .st-key-hero_box {
        background: rgba(20, 32, 28, .94);
        border-color: rgba(255,255,255,.12);
    }
    .auth-shell [data-testid="stWidgetLabel"] p,
    .auth-shell [data-testid="stWidgetLabel"] label,
    .auth-shell .stRadio label,
    .auth-shell [data-baseweb="tab"] { color: #F8FAF9 !important; }
}

/* === RECouvrement UI/UX === */
.home-hero{position:relative;overflow:hidden;margin-bottom:1rem;border-radius:24px;min-height:310px;background:linear-gradient(180deg,rgba(8,24,19,.48),rgba(30,18,11,.82)),url("https://commons.wikimedia.org/wiki/Special:Redirect/file/The%20Avenue%20of%20the%20Baobabs%20in%20Madagascar%20near%20the%20city%20of%20Morondava%20at%20sunrise%20%2825%29.jpg") center/cover no-repeat;box-shadow:0 18px 45px -22px rgba(0,0,0,.5);color:#fff}
.home-hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.08),rgba(0,0,0,.28));pointer-events:none}
.home-hero-content{position:relative;z-index:1;padding:2rem 1.4rem 5.6rem;max-width:680px}.home-hero h1,.home-hero p,.home-hero .eyebrow{color:#fff!important}.home-hero h1{margin:.45rem 0 .6rem;font-size:clamp(1.8rem,4vw,2.65rem);line-height:1.08}.home-hero p{margin:0;max-width:620px;line-height:1.65;color:rgba(255,255,255,.88)!important}.home-hero-status{margin-top:.9rem}
.home-hero-brand{display:flex;align-items:center;gap:.08em;font-weight:800;letter-spacing:.01em}
.home-hero-logo{display:inline-flex;flex:none;width:.9em;height:.9em;border-radius:22%;overflow:hidden;box-shadow:0 4px 14px rgba(0,0,0,.35)}
.home-hero-logo svg{width:100%;height:100%;display:block}
.daily-tip{position:absolute;left:1rem;right:1rem;bottom:1rem;z-index:2;display:flex;gap:.7rem;align-items:flex-start;padding:.9rem 1rem;border-radius:16px;background:var(--lamba);color:#24190B;box-shadow:0 8px 22px rgba(0,0,0,.18)}.daily-tip b,.daily-tip span{color:#24190B!important}.daily-tip .bulb{font-size:1.15rem;line-height:1}
.start-grid,.steps-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem}.start-card,.step-card{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:16px;padding:1rem;box-shadow:0 5px 18px -10px rgba(var(--shadow-rgb),.18)}.start-card h4,.start-card p,.step-card h4,.step-card p{color:var(--ink)!important}.step-number{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--lamba);color:#24190B;font-weight:800;margin-bottom:.55rem}
.auth-form-title{color:var(--ink)!important}.auth-form-subtitle{color:var(--muted)!important}.auth-shell .stTabs [data-baseweb="tab-list"]{gap:.35rem;border-bottom:1px solid var(--line)}.auth-shell .stTabs [data-baseweb="tab"]{color:var(--muted)!important;font-weight:700}.auth-shell .stTabs [aria-selected="true"]{color:var(--ink)!important}
section[data-testid="stSidebar"] div[role="radiogroup"]>label{position:relative;padding-left:2.45rem}section[data-testid="stSidebar"] div[role="radiogroup"]>label::before{position:absolute;left:.75rem;font-size:1rem;opacity:.9}section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-child(1)::before{content:"⌂"}section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-child(2)::before{content:"▦"}section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-child(3)::before{content:"▤"}section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-child(4)::before{content:"⌖"}section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-child(5)::before{content:"◉"}section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-child(6)::before{content:"?"}section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-child(7)::before{content:"○"}.sidebar-logo{align-items:flex-start}.sidebar-logo-sub{color:var(--sidebar-accent);font-size:.55rem;font-weight:800;letter-spacing:.12em;margin-top:.15rem}.st-key-sidebar_logout{border-top:1px solid var(--sidebar-border);margin-top:1rem;padding-top:1rem}
.dashboard-stat.accent,.dashboard-stat.accent *{color:var(--ink)!important}.dashboard-stat.accent{background:var(--lamba-clair)!important;border-color:rgba(230,154,42,.3)!important}
@media(max-width:768px){.start-grid,.steps-grid,.dashboard-stat-grid,.auth-shell,.auth-feature-grid{grid-template-columns:1fr!important}.home-hero{min-height:390px}.home-hero-content{padding:1.35rem 1rem 7rem}.daily-tip{left:.7rem;right:.7rem;bottom:.7rem}.stHorizontalBlock{flex-direction:column!important;gap:.55rem!important}}
@media(max-width:480px){.home-hero h1{font-size:1.8rem}.home-hero{min-height:430px}.block-container{padding-left:.6rem;padding-right:.6rem}}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# 5. SCHEMAS PEDAGOGIQUES PYDANTIC
# =============================================================================

class ErreurDetail(BaseModel):
    erreur: str = Field(description="Erreur dans la phrase")
    correction: str = Field(description="Correction proposee")
    raison: str = Field(description="Regle ou raison")


class PartDecomposition(BaseModel):
    type: str = Field(description="Sujet, Verbe ou Complement")
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
    mot: str = Field(description="Mot ou syllabe mal prononce")
    entendu: str = Field(description="Approximation phonetique de ce qui a ete entendu")
    attendu: str = Field(description="Prononciation correcte attendue")
    conseil: str = Field(description="Conseil precis et actionnable pour corriger")


class ReponsePrononciation(BaseModel):
    score: int = Field(description="Score global de 0 a 100")
    points_forts: list[str]
    fautes: list[FautePrononciation] = Field(description="Liste exacte des fautes de prononciation detectees")
    conseil: str


# =============================================================================
# 6. DONNEES PEDAGOGIQUES
# =============================================================================

MISSIONS = [
    ("Au marche", "Negocier le prix d'un produit avec respect."),
    ("A l'universite", "Se presenter a un enseignant ou a un nouveau camarade."),
    ("Entretien d'embauche", "Repondre a des questions simples et professionnelles."),
    ("Dans la ville", "Demander et comprendre un itineraire."),
    ("A la bibliotheque", "Demander un livre et comprendre les consignes."),
    ("Dans un service public", "Expliquer clairement une demande administrative."),
]

PALIERS = [
    (0, "Palier 1 — Premiers pas", "Termine ta premiere activite pour lancer l'aventure."),
    (20, "Palier 2 — Explorateur", "Continue a t'entrainer en grammaire et en missions."),
    (50, "Palier 3 — Apprenti confirme", "Tu maitrises les bases : attaque la prononciation."),
    (100, "Palier 4 — Orateur", "Enchaine les quiz et les dialogues sans faute."),
    (200, "Palier 5 — Champion FRANTSAY", "Tu es pret a parler francais avec assurance !"),
]

LESSONS = [
    {
        "titre": "Accorder le sujet et le verbe",
        "niveau": "Tous",
        "contenu": "Le verbe s'accorde avec son sujet : 'Je vais', 'Nous allons', 'Les etudiants travaillent'.",
        "exemple": "Les eleves revisent le francais.",
    },
    {
        "titre": "Choisir 'a', 'au', 'aux'",
        "niveau": "Lycee",
        "contenu": "On dit 'a l'universite', 'au marche', 'aux cours'. Le choix depend du nom qui suit.",
        "exemple": "Je vais a l'universite. / Je vais au marche.",
    },
    {
        "titre": "Les articles : un, une, des",
        "niveau": "College",
        "contenu": "'Un' accompagne un nom masculin singulier, 'une' un nom feminin singulier et 'des' le pluriel.",
        "exemple": "un livre, une ecole, des etudiants.",
    },
    {
        "titre": "Relier ses idees",
        "niveau": "Universite",
        "contenu": "Utilise 'parce que', 'donc', 'cependant', 'ensuite' pour construire un discours plus clair.",
        "exemple": "Je travaille, parce que je veux reussir.",
    },
]

MODEL_SENTENCES = {
    "College": [
        "Ma soeur va a l'ecole tous les matins.",
        "Le chat dort sous la table de la cuisine.",
        "J'aime lire des histoires avant de dormir.",
        "Nous jouons au football apres les cours.",
        "Mon pere prepare le riz pour le diner.",
        "La maitresse ecrit la lecon au tableau.",
        "Il pleut beaucoup pendant la saison chaude.",
        "Mes cousins habitent pres du grand marche.",
        "Je range mes cahiers dans mon sac.",
        "Le marchand vend des fruits frais le matin.",
        "Nous chantons une chanson pendant la recreation.",
        "Ma grand-mere raconte de belles histoires le soir.",
    ],
    "Lycee": [
        "Je pense que la lecture developpe l'imagination.",
        "Hier, nous avons visite le marche du village.",
        "Il faut reviser regulierement pour reussir ses examens.",
        "Mes amis et moi preparons un expose sur l'environnement.",
        "Le professeur nous a demande un travail de groupe.",
        "Cette annee, je souhaite ameliorer mon niveau en francais.",
        "Les vacances scolaires approchent a grands pas.",
        "Nous avons discute des problemes de la jeunesse malgache.",
        "Elle a choisi de poursuivre des etudes scientifiques.",
        "Le sport est essentiel pour rester en bonne sante.",
        "Il est important de respecter les horaires des cours.",
        "Nous avons participe a un concours de poesie.",
    ],
    "Universite": [
        "Cette recherche demontre l'importance de la rigueur scientifique.",
        "Le debat portait sur les consequences economiques de la decision.",
        "Il est essentiel d'analyser les sources avant de conclure.",
        "La cooperation internationale reste indispensable au developpement.",
        "Cette etude souligne les enjeux majeurs du developpement durable.",
        "Les chercheurs ont presente leurs conclusions lors du colloque.",
        "La methodologie employee garantit la fiabilite des resultats.",
        "Le memoire doit s'appuyer sur une bibliographie solide.",
        "Cette hypothese merite d'etre verifiee experimentalement.",
        "Les etudiants ont defendu leur projet devant le jury.",
        "L'analyse critique des donnees reste une etape indispensable.",
        "Ce phenomene souleve de nombreuses questions ethiques.",
    ],
}


# =============================================================================
# 7. ETAT DE SESSION + AUTHENTIFICATION SUPABASE
# =============================================================================

DEFAULT_STATE = {
    "level": "Lycee", "score": 0, "questions_done": 0,
    "last_correction": None, "last_dialogue": None,
    "quiz_question": None, "quiz_answer": None,
    "model_sentence": None, "pronunciation_result": None,
    "last_audio_hash": None, "user_email": None, "user_pseudo": None,
    "user_id": None, "auth_user_id": None, "access_token": None,
    "identified": False, "auth_view": "login",
    "nav_page": "Accueil",
    "show_dashboard": False,
    "theme_mode": "auto",
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

apply_theme_preference()


_SECRET_ALIASES: dict[str, list[tuple[str, str]]] = {
    "SUPABASE_URL": [("supabase", "url"), ("supabase", "URL")],
    "SUPABASE_ANON_KEY": [("supabase", "anon_key"), ("supabase", "ANON_KEY"), ("supabase", "anon")],
    "SUPABASE_SERVICE_ROLE_KEY": [
        ("supabase", "service_role_key"),
        ("supabase", "SERVICE_ROLE_KEY"),
        ("supabase", "service_role"),
    ],
    "GEMINI_API_KEY": [("gemini", "api_key"), ("gemini", "API_KEY")],
    "SESSION_ENCRYPTION_KEY": [("session", "encryption_key"), ("encryption", "key")],
}


def _from_nested_secrets(section: str, subkey: str) -> str:
    try:
        section_obj = st.secrets.get(section)
        if section_obj is None:
            return ""
        value = section_obj.get(subkey) if hasattr(section_obj, "get") else section_obj[subkey]
        return str(value).strip() if value is not None else ""
    except Exception:
        return ""


def _secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            value = str(st.secrets[name]).strip()
            if value:
                return value
    except Exception:
        pass

    for section, subkey in _SECRET_ALIASES.get(name, []):
        value = _from_nested_secrets(section, subkey)
        if value:
            return value

    env_value = os.environ.get(name, "").strip()
    if env_value:
        return env_value

    return default


@st.cache_resource(show_spinner=False)
def get_db_client() -> Client:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY manquant.")
    return create_client(url, key)


def get_auth_client() -> Client:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL ou SUPABASE_ANON_KEY manquant.")
    return create_client(url, key)


def get_cookie_manager():
    """Retourne une seule instance CookieManager par session Streamlit.

    extra-streamlit-components utilise ``key="init"`` par defaut.
    Creer plusieurs instances dans une meme execution provoque
    DuplicateWidgetID. Le singleton session_state evite ce conflit.
    """
    if not COOKIE_MANAGER_AVAILABLE:
        return None

    manager = st.session_state.get("_frantsay_cookie_manager")
    if manager is None:
        manager = stx.CookieManager(key="frantsay_cookie_manager")
        st.session_state["_frantsay_cookie_manager"] = manager
    return manager


def _fernet() -> Fernet:
    secret = _secret("SESSION_ENCRYPTION_KEY")
    if not secret:
        raise RuntimeError("SESSION_ENCRYPTION_KEY manquant dans les Secrets Streamlit.")
    try:
        return Fernet(secret.encode())
    except Exception as exc:
        raise RuntimeError("SESSION_ENCRYPTION_KEY doit etre une cle Fernet valide.") from exc


def _hash_sid(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def _extract_first_row(response: Any) -> dict[str, Any] | None:
    data = getattr(response, "data", None) or []
    return data[0] if data else None


_REQUIRED_SECRETS: list[tuple[str, str]] = [
    ("SUPABASE_URL", "URL du projet Supabase"),
    ("SUPABASE_ANON_KEY", "Cle publique (anon) Supabase"),
    ("SUPABASE_SERVICE_ROLE_KEY", "Cle service-role Supabase"),
    ("SESSION_ENCRYPTION_KEY", "Cle de chiffrement des sessions (Fernet)"),
]


def _check_url() -> tuple[bool, str]:
    url = _secret("SUPABASE_URL")
    if not url:
        return False, "absente"
    if not (url.startswith("https://") and ".supabase.co" in url):
        return False, "presente mais mal formee (attendu: https://xxxx.supabase.co)"
    return True, "ok"


def _check_anon_key() -> tuple[bool, str]:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_ANON_KEY")
    if not key:
        return False, "absente"
    if not url:
        return False, "impossible a verifier (URL manquante)"
    try:
        create_client(url, key)
        return True, "ok"
    except Exception as exc:
        return False, f"rejetee a la creation du client ({type(exc).__name__})"


def _check_service_role_key() -> tuple[bool, str]:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        return False, "absente"
    if not url:
        return False, "impossible a verifier (URL manquante)"
    try:
        create_client(url, key)
        return True, "ok"
    except Exception as exc:
        return False, f"rejetee a la creation du client ({type(exc).__name__})"


def _check_encryption_key() -> tuple[bool, str]:
    secret = _secret("SESSION_ENCRYPTION_KEY")
    if not secret:
        return False, "absente"
    try:
        Fernet(secret.encode())
        return True, "ok"
    except Exception:
        return False, "presente mais invalide (doit etre une cle Fernet base64, 32 bytes)"


_SECRET_CHECKS = {
    "SUPABASE_URL": _check_url,
    "SUPABASE_ANON_KEY": _check_anon_key,
    "SUPABASE_SERVICE_ROLE_KEY": _check_service_role_key,
    "SESSION_ENCRYPTION_KEY": _check_encryption_key,
}


def secrets_status() -> list[tuple[str, str, bool, str]]:
    results = []
    for name, label in _REQUIRED_SECRETS:
        ok, reason = _SECRET_CHECKS[name]()
        results.append((name, label, ok, reason))
    return results


def supabase_ready() -> bool:
    try:
        get_db_client()
        get_auth_client()
        _fernet()
        return True
    except Exception:
        return False


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._%+-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$")
PSEUDO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_pseudo(pseudo: str) -> str:
    return re.sub(r"\s+", " ", pseudo.strip())


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(value)) and ".." not in value


def is_valid_pseudo(value: str) -> bool:
    return bool(PSEUDO_PATTERN.fullmatch(value))


def find_profile_by_auth_id(auth_user_id: str) -> dict[str, Any] | None:
    return _extract_first_row(
        get_db_client().table("users")
        .select("id,auth_user_id,email,pseudo,display_name,level,score,questions_done,progress")
        .eq("auth_user_id", str(auth_user_id))
        .limit(1)
        .execute()
    )


def create_profile(auth_user_id: str, email: str, level: str, pseudo: str = "") -> dict[str, Any]:
    if level not in LEVELS:
        raise ValueError("Niveau invalide.")
    if pseudo and not is_valid_pseudo(pseudo):
        raise ValueError("Pseudo invalide : 3 a 24 caracteres, lettres/chiffres/_/.- uniquement.")
    payload = {
        "auth_user_id": str(auth_user_id),
        "email": normalize_email(email),
        "display_name": normalize_pseudo(pseudo) if pseudo else None,
        "pseudo": normalize_pseudo(pseudo) if pseudo else None,
        "level": level,
        "score": 0,
        "questions_done": 0,
        "progress": {"score": 0, "questions_done": 0},
    }
    user = _extract_first_row(
        get_db_client().table("users")
        .insert(payload)
        .execute()
    )
    if not user:
        raise RuntimeError("Le profil n'a pas pu etre cree.")
    return user


def restore_profile(user: dict[str, Any], access_token: str) -> None:
    progress = user.get("progress") or {}
    level = str(user.get("level") or "")
    if level not in LEVELS:
        raise ValueError("Le profil ne possede pas un niveau d'etudes valide.")
    st.session_state.user_id = str(user["id"])
    st.session_state.auth_user_id = str(user["auth_user_id"])
    st.session_state.user_email = str(user.get("email") or "")
    st.session_state.user_pseudo = str(user.get("display_name") or user.get("pseudo") or "")
    st.session_state.level = level
    st.session_state.score = int(progress.get("score", user.get("score", 0)) or 0)
    st.session_state.questions_done = int(progress.get("questions_done", user.get("questions_done", 0)) or 0)
    st.session_state.theme_mode = str(progress.get("theme_mode") or "auto")
    st.session_state.access_token = access_token
    st.session_state.model_sentence = random.choice(MODEL_SENTENCES[level])
    st.session_state.identified = True


def create_login_session(auth_user_id: str, refresh_token: str) -> None:
    session_id = uuid.uuid4().hex + uuid.uuid4().hex
    get_db_client().table("app_sessions").insert({
        "session_id_hash": _hash_sid(session_id),
        "auth_user_id": str(auth_user_id),
        "refresh_token_enc": _fernet().encrypt(refresh_token.encode()).decode(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
    }).execute()
    cm = get_cookie_manager()
    if cm is not None:
        try:
            cm.set(SESSION_COOKIE_NAME, session_id, key="frantsay_session_set", expires_at=datetime.now() + timedelta(days=30), max_age=30 * 24 * 60 * 60, secure=True, same_site="lax")
        except Exception:
            pass
    st.query_params["frantsay_sid"] = session_id


def delete_login_session(session_id: str | None) -> None:
    if not session_id:
        return
    try:
        get_db_client().table("app_sessions").delete().eq("session_id_hash", _hash_sid(session_id)).execute()
    finally:
        cm = get_cookie_manager()
        if cm is not None:
            try:
                cm.delete(SESSION_COOKIE_NAME, key="frantsay_session_delete")
            except Exception:
                pass
        try:
            st.query_params.pop("frantsay_sid", None)
        except Exception:
            pass


def restore_from_cookie() -> bool:
    sid = None
    cm = get_cookie_manager()
    if cm is not None:
        try:
            sid = cm.get(SESSION_COOKIE_NAME)
        except Exception:
            sid = None
    if not sid:
        sid = st.query_params.get("frantsay_sid")
    if not sid or not isinstance(sid, str):
        return False
    try:
        row = _extract_first_row(
            get_db_client().table("app_sessions")
            .select("session_id_hash,auth_user_id,refresh_token_enc,expires_at")
            .eq("session_id_hash", _hash_sid(sid))
            .limit(1)
            .execute()
        )
        if not row:
            return False
        expires_at = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
        if expires_at <= datetime.now(timezone.utc):
            delete_login_session(sid)
            return False
        refresh_token = _fernet().decrypt(str(row["refresh_token_enc"]).encode()).decode()
        auth = get_auth_client()
        refreshed = auth.auth.refresh_session(refresh_token)
        session = getattr(refreshed, "session", None)
        user_obj = getattr(refreshed, "user", None)
        if not session or not user_obj:
            delete_login_session(sid)
            return False
        access_token = str(getattr(session, "access_token", ""))
        new_refresh = str(getattr(session, "refresh_token", ""))
        if not access_token or not new_refresh:
            delete_login_session(sid)
            return False
        verified = auth.auth.get_user(access_token)
        verified_user = getattr(verified, "user", None)
        if not verified_user or str(getattr(verified_user, "id", "")) != str(row["auth_user_id"]):
            delete_login_session(sid)
            return False
        get_db_client().table("app_sessions").update({
            "refresh_token_enc": _fernet().encrypt(new_refresh.encode()).decode(),
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }).eq("session_id_hash", _hash_sid(sid)).execute()
        profile = find_profile_by_auth_id(str(row["auth_user_id"]))
        if not profile:
            delete_login_session(sid)
            return False
        restore_profile(profile, access_token)
        create_login_session(str(row["auth_user_id"]), new_refresh)
        return True
    except (InvalidToken, Exception):
        return False


def sign_in(email: str, password: str) -> None:
    email = normalize_email(email)
    if not is_valid_email(email):
        raise ValueError("Saisis une adresse e-mail valide.")
    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caracteres.")
    response = get_auth_client().auth.sign_in_with_password({"email": email, "password": password})
    session = getattr(response, "session", None)
    user_obj = getattr(response, "user", None)
    if not session or not user_obj:
        raise ValueError("Connexion impossible. Verifie ton e-mail et ton mot de passe.")
    access_token = str(getattr(session, "access_token", ""))
    refresh_token = str(getattr(session, "refresh_token", ""))
    auth_user_id = str(getattr(user_obj, "id", ""))
    profile = find_profile_by_auth_id(auth_user_id)
    if not access_token or not refresh_token or not auth_user_id or not profile:
        raise ValueError("Ton compte n'est pas correctement configure dans FRANTSAY.")
    create_login_session(auth_user_id, refresh_token)
    restore_profile(profile, access_token)


def sign_up(email: str, password: str, confirm: str, pseudo: str, level: str) -> str:
    email = normalize_email(email)
    pseudo = normalize_pseudo(pseudo)
    if not is_valid_email(email):
        raise ValueError("Saisis une adresse e-mail valide.")
    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caracteres.")
    if password != confirm:
        raise ValueError("Les deux mots de passe ne correspondent pas.")
    if pseudo and not is_valid_pseudo(pseudo):
        raise ValueError("Pseudo invalide : 3 a 24 caracteres, lettres/chiffres/_/.- uniquement.")
    if level not in LEVELS:
        raise ValueError("Choisis ton niveau d'etudes.")
    response = get_auth_client().auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": {"display_name": pseudo, "study_level": level}}
    })
    user_obj = getattr(response, "user", None)
    session = getattr(response, "session", None)
    if not user_obj:
        raise ValueError("L'inscription n'a pas pu etre creee.")
    auth_user_id = str(getattr(user_obj, "id", ""))
    if find_profile_by_auth_id(auth_user_id):
        return "Compte deja configure. Confirme ton e-mail puis connecte-toi."
    create_profile(auth_user_id, email, level, pseudo)
    if session:
        access_token = str(getattr(session, "access_token", ""))
        refresh_token = str(getattr(session, "refresh_token", ""))
        if access_token and refresh_token:
            create_login_session(auth_user_id, refresh_token)
            restore_profile(find_profile_by_auth_id(auth_user_id), access_token)
            return "Compte cree. Bienvenue dans FRANTSAY."
    return "Compte cree. Verifie ton e-mail avant de te connecter."


def current_progress() -> dict[str, Any]:
    return {
        "score": int(st.session_state.score),
        "questions_done": int(st.session_state.questions_done),
        "theme_mode": st.session_state.get("theme_mode", "auto"),
    }


def save_progress(user_id: str, data: dict[str, Any]) -> None:
    if not user_id:
        raise ValueError("user_id manquant.")
    score = max(0, int(data.get("score", 0)))
    done = max(0, int(data.get("questions_done", 0)))
    progress_payload = {
        "score": score,
        "questions_done": done,
        "theme_mode": data.get("theme_mode", "auto"),
    }
    get_db_client().table("users").update({
        "score": score,
        "questions_done": done,
        "progress": progress_payload,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", user_id).execute()


def save_current_progress() -> None:
    if not st.session_state.get("identified") or not st.session_state.get("user_id"):
        return
    try:
        save_progress(st.session_state.user_id, current_progress())
    except Exception as exc:
        st.warning(f"La progression n'a pas pu etre synchronisee : {exc}")


def update_pseudo(user_id: str, new_pseudo: str) -> None:
    """Met a jour le pseudo/nom affiche du profil connecte (colonnes pseudo + display_name)."""
    if not user_id:
        raise ValueError("user_id manquant.")
    new_pseudo = normalize_pseudo(new_pseudo)
    if new_pseudo and not is_valid_pseudo(new_pseudo):
        raise ValueError("Pseudo invalide : 3 a 24 caracteres, lettres/chiffres/_/.- uniquement.")
    get_db_client().table("users").update({
        "pseudo": new_pseudo or None,
        "display_name": new_pseudo or None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", user_id).execute()
    st.session_state.user_pseudo = new_pseudo


def logout_user() -> None:
    sid = None
    cm = get_cookie_manager()
    if cm is not None:
        try:
            sid = cm.get(SESSION_COOKIE_NAME)
        except Exception:
            sid = None
    if not sid:
        sid = st.query_params.get("frantsay_sid")
    delete_login_session(sid)
    st.session_state.clear()
    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value
    st.session_state.model_sentence = random.choice(MODEL_SENTENCES["Lycee"])


def handle_email_confirmation_link() -> bool:
    token_hash = st.query_params.get("token_hash")
    otp_type = st.query_params.get("type")
    if not token_hash or not otp_type:
        return False
    try:
        response = get_auth_client().auth.verify_otp({"type": otp_type, "token_hash": token_hash})
        session = getattr(response, "session", None)
        user_obj = getattr(response, "user", None)
        if not session or not user_obj:
            st.session_state.email_confirm_error = "Ce lien de confirmation n'est plus valide."
            return False
        access_token = str(getattr(session, "access_token", ""))
        refresh_token = str(getattr(session, "refresh_token", ""))
        auth_user_id = str(getattr(user_obj, "id", ""))
        if not access_token or not refresh_token or not auth_user_id:
            st.session_state.email_confirm_error = "Ce lien de confirmation n'est plus valide."
            return False
        profile = find_profile_by_auth_id(auth_user_id)
        if not profile:
            st.session_state.email_confirm_error = (
                "Ton adresse e-mail est confirmee, mais ton profil est introuvable. "
                "Essaie de te connecter directement."
            )
            return False
        create_login_session(auth_user_id, refresh_token)
        restore_profile(profile, access_token)
        return True
    except Exception:
        st.session_state.email_confirm_error = (
            "Ce lien de confirmation a expire ou a deja ete utilise. "
            "Reessaie de te connecter, ou demande un nouveau lien."
        )
        return False
    finally:
        st.query_params.pop("token_hash", None)
        st.query_params.pop("type", None)


if not st.session_state.identified:
    if handle_email_confirmation_link():
        st.rerun()
    restore_from_cookie()


# =============================================================================
# 8. ECRAN D'AUTHENTIFICATION
# =============================================================================

def render_auth_screen() -> None:
    components.html(
        """<script>
        (function () {
            window.parent.document.body.classList.add("frantsay-auth");
        })();
        </script>""",
        height=0,
    )
    components.html(LEMUR_CLICK_JS, height=0)

    with st.container(key="auth_hero"):
        st.markdown(
            f"""<div class="auth-shell">
                <div class="auth-copy">
                    <div class="brand-lockup">{LEMUR_SVG}
                        <div>
                            <div class="brand-name">FRANTSAY</div>
                            <div class="brand-kicker">APPRENDRE - PRATIQUER - PROGRESSER</div>
                        </div>
                    </div>
                    <div class="auth-copy-body">
                        <div class="auth-kicker">Ta nouvelle facon d'apprendre</div>
                        <h1 class="auth-main-title">Apprendre le francais<br><span>autrement.</span></h1>
                        <p class="auth-main-sub">Une plateforme pensee pour apprendre a ton rythme, 
                        pratiquer avec intelligence et voir tes progres prendre forme.</p>
                    </div>
                </div>
                <div class="auth-panel">
                    <div class="auth-panel-top">
                        <div>
                            <div class="auth-welcome">Bienvenue !</div>
                            <div class="auth-welcome-sub">Ton espace d'apprentissage t'attend.</div>
                        </div>
                        <div class="secure-pill">
                            <span class="secure-dot"></span> Chiffrement de bout en bout
                        </div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    if not supabase_ready():
        st.markdown(
            """
            <div class="maintenance-screen">
                <div class="maintenance-badge">
                    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L4 6v6c0 5 3.4 9.2 8 10 4.6-.8 8-5 8-10V6l-8-4z" stroke="white" stroke-width="1.6" stroke-linejoin="round"/>
                        <path d="M9 12l2 2 4-4.5" stroke="white" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="maintenance-title">FRANTSAY fait une pause technique</div>
                <div class="maintenance-sub">
                    On ajuste quelques reglages cote serveur. Reviens dans quelques
                    instants — tes lecons et ta progression t'attendent toujours.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _admin_token = _secret("ADMIN_DIAG_TOKEN", "frantsay-diag")
        if st.query_params.get("diag") == _admin_token:
            with st.expander("Diagnostic technique (visible uniquement avec le code admin)", expanded=True):
                for name, label, ok, reason in secrets_status():
                    icon = "🟢" if ok else "🔴"
                    st.markdown(f"{icon} **`{name}`** — {label} — *{reason}*")
                st.caption(
                    "Aucune valeur de secret n'est jamais affichee, seulement leur "
                    "presence/validite. Cles acceptees a plat (SUPABASE_URL = \"...\"), "
                    "en section imbriquee ([supabase] puis url = \"...\"), ou en "
                    "variable d'environnement systeme du meme nom."
                )
        st.stop()

    col_left, col_right = st.columns([1.15, 1], gap="large")

    with col_left:
        st.markdown(
            '<div class="auth-form-title">Ton espace personnel</div>'
            '<div class="auth-form-subtitle">Connecte-toi avec ton e-mail et ton mot de passe.</div>',
            unsafe_allow_html=True,
        )

        confirm_error = st.session_state.pop("email_confirm_error", None)
        if confirm_error:
            st.error(confirm_error)

        auth_tabs = st.tabs(["Se connecter", "Créer un compte"])
        with auth_tabs[0]:
            with st.form("login_form"):
                email_input = st.text_input("E-mail", autocomplete="email", placeholder="exemple@email.com")
                password_input = st.text_input("Mot de passe", type="password", autocomplete="current-password")
                submitted = st.form_submit_button("Se connecter", use_container_width=True)
            if submitted:
                try:
                    with st.spinner("Ouverture de ton espace..."):
                        sign_in(email_input or "", password_input or "")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with auth_tabs[1]:
            with st.form("registration_form"):
                email_input = st.text_input("E-mail", autocomplete="email", placeholder="exemple@email.com")
                pseudo_input = st.text_input("Pseudo (facultatif)", autocomplete="username", placeholder="Visible dans ton profil")
                password_input = st.text_input("Mot de passe", type="password", autocomplete="new-password")
                confirm_input = st.text_input("Confirmer le mot de passe", type="password", autocomplete="new-password")
                level_input = st.radio("Ton niveau d'etudes", LEVELS, horizontal=True)
                submitted = st.form_submit_button("Créer mon compte", use_container_width=True)
            if submitted:
                try:
                    with st.spinner("Creation de ton espace..."):
                        message = sign_up(email_input or "", password_input or "", confirm_input or "", pseudo_input or "", level_input)
                    if st.session_state.get("identified"):
                        st.rerun()
                    st.success(message)
                except Exception as exc:
                    st.error(str(exc))

    with col_right:
        st.markdown(
            '<div class="auth-trust-line"><span>✓</span><b>Chiffrement de bout en bout actif</b><small>Ton parcours reste privé, à chaque instant.</small></div>',
            unsafe_allow_html=True,
        )

    st.stop()


if not st.session_state.identified:
    render_auth_screen()

# =============================================================================
# 9. CONFIGURATION SESSION UTILISATEUR CONNECTE
# =============================================================================

level = st.session_state.level


# =============================================================================
# 10. APPELS API GEMINI — AVEC CACHING POUR PERFORMANCE
# =============================================================================

def get_api_key() -> str:
    return _secret("GEMINI_API_KEY")


def api_available() -> bool:
    return bool(get_api_key())


@st.cache_data(show_spinner=False, ttl=3600)
def _call_gemini_structured_cached(system_prompt: str, user_prompt: str, schema_json: str):
    key = get_api_key()
    if not key:
        raise ValueError("Cle API Gemini manquante cote serveur (st.secrets).")
    client = genai.Client(api_key=key)
    schema_dict = json.loads(schema_json)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema_dict,
        ),
    )
    return response.text


def call_gemini_structured(system_prompt: str, user_prompt: str, schema_class):
    key = get_api_key()
    if not key:
        raise ValueError("Cle API Gemini manquante cote serveur (st.secrets).")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema_class,
        ),
    )
    return json.loads(response.text)


@st.cache_data(show_spinner=False, ttl=3600)
def _call_gemini_text_cached(system_prompt: str, user_prompt: str) -> str:
    key = get_api_key()
    if not key:
        raise ValueError("Cle API Gemini manquante cote serveur (st.secrets).")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config={"system_instruction": system_prompt},
    )
    return getattr(response, "text", "").strip()


def call_gemini_text(system_prompt: str, user_prompt: str) -> str:
    key = get_api_key()
    if not key:
        raise ValueError("Cle API Gemini manquante cote serveur (st.secrets).")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config={"system_instruction": system_prompt},
    )
    return getattr(response, "text", "").strip()


def call_gemini_audio_structured(system_prompt: str, audio_bytes: bytes, mime_type: str, extra_text: str, schema_class):
    key = get_api_key()
    if not key:
        raise ValueError("Cle API Gemini manquante cote serveur (st.secrets).")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            extra_text,
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
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
        '<div class="tip"><span class="tag tag-amber">ATT</span> '
        "Les administrateurs sont en train d'activer l'IA, patientez s'il vous plait. "
        "En attendant, les fiches de l'onglet Accueil restent consultables sans IA.</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# 11. PROMPTS SYSTEME
# =============================================================================

CORRECTION_PROMPT = """
Tu es un professeur de francais specialise dans l'enseignement aux apprenants malgaches.
Tu dois corriger sans humilier. Explique simplement l'erreur et donne une regle memorisable.
Prends en compte les difficultes possibles : ordre des mots influence par le malagasy,
genre des noms, articles, conjugaison, prepositions, accords et prononciation.
"""

DIALOGUE_PROMPT = """
Tu es un professeur de francais FLE et tu crees des situations utiles a Madagascar.
Genere un dialogue naturel de 8 a 10 repliques adapte au niveau demande.
Evite le francais artificiel. Ajoute quelques expressions reellement utiles.
Structure en Markdown avec exactement :
## Dialogue
## Vocabulaire a retenir
## Point de grammaire
## Defi
"""

QUIZ_PROMPT = "Cree une seule question de francais adaptee au niveau indique."

PRONONCIATION_PROMPT = """
Tu es un expert en phonetique francaise qui evalue des apprenants malgaches.
On te donne un enregistrement audio et la phrase modele que l'apprenant devait lire a voix haute.
Compare precisement ce qui a ete prononce a la phrase attendue.
Liste UNIQUEMENT les fautes reelles et exactes que tu entends (mot par mot ou syllabe par syllabe),
avec ce qui a ete entendu, ce qui etait attendu, et un conseil concret pour corriger.
Ne liste pas de fautes si la prononciation est correcte. Le score est de 0 a 100.
"""


def level_instruction(level: str) -> str:
    rules = {
        "College": "Utilise un vocabulaire simple, des phrases courtes et des explications concretes adaptees a un collegien.",
        "Lycee": "Utilise un vocabulaire intermediaire, explique les regles avec precision et propose des exemples adaptes au lycee.",
        "Universite": "Utilise un vocabulaire plus riche, des nuances grammaticales et des explications structurees adaptees a l'universite.",
    }
    return rules.get(level, rules["Lycee"])


def prompt_with_level(base: str) -> str:
    return base + "\n\nNIVEAU PEDAGOGIQUE VERROUILLE : " + st.session_state.level + "\n" + level_instruction(st.session_state.level)


def reset_quiz():
    st.session_state.quiz_question = None
    st.session_state.pop("quiz_answer", None)


# =============================================================================
# 12bis. CONSEIL DU JOUR — banque variee, selection deterministe par date
# =============================================================================

DAILY_TIPS = [
    "Lis une phrase à voix haute, puis réutilise-la dans une situation réelle. La régularité compte plus que la quantité.",
    "Note trois mots nouveaux avant de dormir : la mémoire les consolide pendant la nuit.",
    "Raconte ta journée en français en une seule phrase, même simple : la constance vaut mieux que la perfection.",
    "Enregistre-toi en train de parler, puis réécoute-toi : tu détecteras des fautes que tu n'entends pas en direct.",
    "Change l'ordre des mots dans une phrase apprise pour vérifier que tu en comprends vraiment la structure.",
    "Associe chaque mot nouveau à une image mentale précise plutôt qu'à sa traduction seule.",
    "Reformule à voix haute une explication de grammaire avec tes propres mots pour vérifier que tu l'as comprise.",
    "Fixe-toi une micro-session de 5 minutes plutôt qu'une longue session rare : la régularité ancre mieux les acquis.",
    "Repère un mot que tu confonds souvent et écris une phrase qui t'aide à ne plus l'oublier.",
    "Avant de deviner un mot inconnu, essaie d'abord de comprendre le sens général de la phrase qui l'entoure.",
    "Relis une phrase que tu as ratée hier : la répétition espacée fixe mieux l'information que la répétition immédiate.",
    "Essaie de traduire une pensée simple sans passer par ta langue maternelle, directement en français.",
    "Choisis un mot du jour et utilise-le volontairement trois fois dans des phrases différentes.",
    "Ferme les yeux et récite la dernière phrase apprise de mémoire, sans regarder l'écran.",
]


def get_daily_tip() -> str:
    """Selectionne un conseil du jour de maniere deterministe (meme conseil toute la journee,
    change chaque jour) a partir d'une graine pseudo-aleatoire basee sur la date du jour."""
    seed = datetime.now().date().toordinal()
    return random.Random(seed).choice(DAILY_TIPS)


# =============================================================================
# 12. SIDEBAR
# =============================================================================

NAV_PAGES = ["Accueil", "Tableau de bord", "Grammaire", "Missions", "Prononciation", "Quiz", "Paramètres"]

with st.sidebar:
    st.markdown(
        f'<div class="sidebar-logo"><div class="sidebar-logo-mark">{FRANTSAY_LOGO_SVG}</div>'
        '<div><div class="sidebar-logo-word">FRANTSAY</div></div></div>',
        unsafe_allow_html=True,
    )

    _current_nav = st.session_state.nav_page if st.session_state.nav_page in NAV_PAGES else "Accueil"
    selected_page = st.radio(
        "Navigation",
        options=NAV_PAGES,
        index=NAV_PAGES.index(_current_nav),
        key="nav_radio",
        label_visibility="collapsed",
    )
    if selected_page != st.session_state.nav_page:
        st.session_state.nav_page = selected_page
        st.rerun()

    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

    with st.container(key="sidebar_logout"):
        if st.button("↪  Se déconnecter", key="logout_button", use_container_width=True):
            logout_user()
            st.rerun()


# =============================================================================
# 13. CONTENU DES PAGES (navigation uniquement dans la sidebar)
# =============================================================================

if st.session_state.nav_page == "Accueil":
    status = ('<span class="badge badge-ok"><span class="dot"></span>Assistant IA actif</span>' if api_available() else '<span class="badge badge-warn">Cours disponibles — IA non activée</span>')
    daily_tip = safe_html(get_daily_tip())
    st.markdown(f'''<section class="home-hero"><div class="home-hero-content"><div style="display: flex; align-items: center; gap: 4px; margin-bottom: 15px;">{FRANTSAY_LOGO_SVG}<span style="font-size: 3rem; font-weight: 900; color: #FFFFFF; letter-spacing: -1px; line-height: 1;">RANTSAY</span></div><p>Apprendre le français autrement</p><div class="home-hero-status">{status}</div></div><div class="daily-tip"><span class="bulb">💡</span><div><b>Conseil du jour</b><br><span>{daily_tip}</span></div></div></section>''', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span class="eyebrow">COMMENCER</span><h3>Choisis ton prochain pas</h3></div>', unsafe_allow_html=True)
    st.markdown('''<div class="start-grid"><div class="start-card"><span class="tag tag-solid">01</span><h4>Grammaire</h4><p>Comprends les règles et corrige tes phrases.</p></div><div class="start-card"><span class="tag tag-green">02</span><h4>Missions</h4><p>Pratique avec des situations utiles du quotidien.</p></div><div class="start-card"><span class="tag tag-amber">03</span><h4>Prononciation</h4><p>Lis à voix haute et reçois un retour automatique.</p></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="margin-top:1.25rem"><span class="eyebrow">PARCOURS</span><h3>Comment ça marche ?</h3></div>', unsafe_allow_html=True)
    st.markdown('''<div class="steps-grid"><div class="step-card"><span class="step-number">1</span><h4>Explore</h4><p>Accède directement aux modules de Grammaire, Missions, Prononciation ou Quiz depuis le menu.</p></div><div class="step-card"><span class="step-number">2</span><h4>Pratique</h4><p>Travaille avec des exercices courts, des exemples et des situations concrètes.</p></div><div class="step-card"><span class="step-number">3</span><h4>Progresse</h4><p>Consulte ton tableau de bord pour suivre tes performances et tes paliers.</p></div></div>''', unsafe_allow_html=True)

elif st.session_state.nav_page == "Tableau de bord":
    # Espace prive : suivi detaille (score, progression, statistiques).
    score = st.session_state.score
    st.markdown(
        '<div class="card"><span class="eyebrow">Espace prive</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Ton tableau de bord</h3>'
        '<p style="margin:0;font-size:.8rem;color:var(--muted)">Le suivi detaille de ta progression.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""<div class="dashboard-stat-grid">
            <div class="dashboard-stat">
                <span>PROGRESSION</span>
                <b>{min(100, max(0, score))}%</b>
                <small>Continue comme ca</small>
            </div>
            <div class="dashboard-stat">
                <span>POINTS</span>
                <b>{score:,}</b>
                <small>Points gagnes</small>
            </div>
            <div class="dashboard-stat">
                <span>ACTIVITES</span>
                <b>{st.session_state.questions_done}</b>
                <small>Defis realises</small>
            </div>
            <div class="dashboard-stat accent">
                <span>OBJECTIF</span>
                <b>En route</b>
                <small>Ton parcours avance</small>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="card" style="margin-top:1rem"><span class="eyebrow">Progression</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Ton parcours de defis</h3>'
        f'<p style="margin:0;font-size:.8rem;color:var(--muted)">Gagne des points en grammaire, '
        f"missions, prononciation et quiz pour debloquer chaque palier. Score actuel : <b>{score}</b> pts.</p></div>",
        unsafe_allow_html=True,
    )

    cards = []
    for i, (seuil, titre, desc) in enumerate(PALIERS):
        next_seuil = PALIERS[i + 1][0] if i + 1 < len(PALIERS) else None
        unlocked = score >= seuil
        completed = unlocked and next_seuil is not None and score >= next_seuil

        if completed:
            tag_html = '<span class="tag tag-green">TERMINE</span>'
        elif unlocked:
            tag_html = '<span class="tag tag-solid">EN COURS</span>'
        else:
            tag_html = '<span class="tag tag-muted">VERROUILLE</span>'

        progress_html = ""
        if unlocked and not completed and next_seuil is not None:
            pct = max(0, min(100, round((score - seuil) / (next_seuil - seuil) * 100)))
            progress_html = (
                f'<div class="palier-progress">'
                f'<div class="palier-progress-bar" style="width:{pct}%"></div></div>'
            )

        cards.append(
            f'<div class="lesson" style="{"" if unlocked else "opacity:.55"}">'
            f'<span class="eyebrow">{tag_html}</span>'
            f'<b>{safe_html(titre)}</b>'
            f'<p>{safe_html(desc)}</p>'
            f'{progress_html}'
            '</div>'
        )
    st.markdown("".join(cards), unsafe_allow_html=True)


elif st.session_state.nav_page == "Grammaire":
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag">01</span>Grammaire</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Corrige ma phrase</h3>'
        '<p style="margin:0;font-size:.8rem;color:var(--muted)">Ecris une phrase comme tu la dirais naturellement.</p></div>',
        unsafe_allow_html=True,
    )

    text = st.text_area(
        "Phrase",
        placeholder="Exemple : Hier, je suis alle au marche avec mes amis.",
        height=100,
        label_visibility="collapsed",
    )

    if not api_available():
        show_api_notice()

    if st.button("Analyser ma phrase", key="analyze"):
        if not text.strip():
            st.warning("Ecris d'abord une phrase.")
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
                st.toast("Analyse terminee !")
            except Exception as exc:
                st.error(f"Erreur d'analyse : {exc}")

    result = st.session_state.last_correction
    if result:
        st.markdown(
            '<div class="card"><span class="eyebrow"><span class="tag tag-green">OK</span>Resultat</span>'
            '<h4 style="margin:.2rem 0">' + safe_html(result.get("phrase_corrigee", "")) + "</h4></div>",
            unsafe_allow_html=True,
        )

        parts = result.get("decomposition", [])
        if parts:
            mapping = {"Sujet": "sujet", "Verbe": "verbe", "Complement": "complement"}
            html_parts = '<div class="card"><h4 style="margin:.1rem 0 .4rem 0;font-size:.9rem">Decomposition</h4>'
            for part in parts:
                typ = str(part.get("type", "Autre"))
                cls = mapping.get(typ, "autre")
                html_parts += (
                    f'<div class="capsule {cls}">'
                    f'<span class="capsule-type">{safe_html(typ)}</span>'
                    f'<span class="capsule-text">{safe_html(part.get("texte", ""))}</span>'
                    '</div>'
                )
            html_parts += "</div>"
            st.markdown(html_parts, unsafe_allow_html=True)

        st.markdown('<div class="card"><h4 style="margin:.1rem 0 .4rem 0;font-size:.9rem">Explication</h4>', unsafe_allow_html=True)
        st.write(result.get("explication", ""))

        errors = result.get("erreurs", [])
        if errors:
            st.markdown("**Erreurs reperes**")
            for err in errors:
                st.markdown(
                    f"- **{err.get('erreur','')}** -> {err.get('correction','')}  \n"
                    f"  *Pourquoi ?* {err.get('raison','')}"
                )

        st.markdown(f"**Prononciation :** {result.get('conseil_prononciation', '')}")
        st.markdown(f"**Mini-exercice :** {result.get('mini_exercice', '')}")
        st.markdown("</div>", unsafe_allow_html=True)


elif st.session_state.nav_page == "Missions":
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag tag-green">02</span>Missions</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Parler dans la vraie vie</h3></div>',
        unsafe_allow_html=True,
    )

    mission_names = [x[0] for x in MISSIONS]
    selected_name = st.selectbox("Mission", mission_names)
    selected_desc = dict(MISSIONS)[selected_name]

    st.markdown(f'<div class="tip"><b>Situation :</b> {safe_html(selected_desc)}</div>', unsafe_allow_html=True)

    if not api_available():
        show_api_notice()

    if st.button("Generer mon dialogue", key="dialogue"):
        if not api_available():
            show_api_notice()
        else:
            try:
                with st.spinner("Creation de la situation..."):
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


elif st.session_state.nav_page == "Prononciation":
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag tag-amber">03</span>Prononciation interactive</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Entraine ta prononciation</h3></div>',
        unsafe_allow_html=True,
    )

    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🔄 Nouvelle phrase", key="new_sentence_btn"):
            st.session_state.model_sentence = random.choice(MODEL_SENTENCES[level])
            st.session_state.pronunciation_result = None
    with colB:
        listen_model = st.button("🔊 Écouter le modèle", key="listen_model_btn")

    st.markdown(
        '<div class="phrase-modele">'
        '<span class="eyebrow2">Phrase a lire a voix haute</span>'
        f'<h3>" {safe_html(st.session_state.model_sentence)} "</h3>'
        '</div>',
        unsafe_allow_html=True,
    )

    if listen_model:
        try:
            st.audio(make_audio(st.session_state.model_sentence), format="audio/mp3")
        except Exception as exc:
            st.error(f"Audio indisponible : {exc}")

    st.markdown(
        '<div class="card"><span class="eyebrow">A toi de parler</span>'
        '<h4 style="margin:.2rem 0;font-size:.95rem">Enregistre-toi</h4>'
        '<p style="margin:0;font-size:.76rem;color:var(--muted)">'
        "Appuie sur le bouton ci-dessous pour enregistrer ta voix, puis relache pour envoyer l'analyse automatique. "
        "L'analyse demarre automatiquement.</p></div>",
        unsafe_allow_html=True,
    )

    if MIC_RECORDER_AVAILABLE:
        audio = mic_recorder(start_prompt="🎙️ Démarrer l'enregistrement", stop_prompt="⏹️ Arrêter et Analyser", just_once=True, use_container_width=True, format="wav", key="pronunciation_recorder")
        if audio and audio.get("bytes"):
            audio_bytes = audio["bytes"]
            audio_id = str(audio.get("id", hashlib.md5(audio_bytes).hexdigest()))
            if audio_id != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = audio_id
                st.session_state.recording_status = "Capture terminée — analyse IA en cours…"
                if not api_available():
                    show_api_notice()
                else:
                    try:
                        with st.spinner("Analyse automatique de ta prononciation..."):
                            pronunciation_result = call_gemini_audio_structured(PRONONCIATION_PROMPT, audio_bytes, "audio/wav", f"Phrase modele attendue : {st.session_state.model_sentence}", ReponsePrononciation)
                        st.session_state.pronunciation_result = pronunciation_result
                        st.session_state.questions_done += 1
                        st.session_state.score += max(0, int(pronunciation_result.get("score", 0)) // 10)
                        st.session_state.recording_status = "Analyse terminée."
                        save_current_progress()
                    except Exception as exc:
                        st.session_state.recording_status = "Analyse impossible."
                        st.error(f"Erreur lors de l'analyse vocale : {exc}")
            st.audio(audio_bytes, format="audio/wav")
    else:
        st.warning("Le module d'enregistrement n'est pas installé. Ajoute `streamlit-mic-recorder` aux dépendances du projet.")

    pronunciation_result = st.session_state.pronunciation_result
    if pronunciation_result:
        st.markdown('<div class="card"><h4 style="margin:.1rem 0 .5rem 0;font-size:.95rem">Resultat</h4>', unsafe_allow_html=True)
        st.metric("Score de prononciation", f"{pronunciation_result.get('score', 0)}/100")

        for point in pronunciation_result.get("points_forts", []):
            st.markdown(f'<span class="tag tag-green">OK</span> {safe_html(point)}', unsafe_allow_html=True)

        fautes = pronunciation_result.get("fautes", [])
        if fautes:
            st.markdown("**Fautes precises detectees**")
            for f in fautes:
                st.markdown(
                    '<div class="faute">'
                    f'<span class="mot">{safe_html(f.get("mot",""))}</span> - '
                    f'entendu : " {safe_html(f.get("entendu",""))} ", attendu : " {safe_html(f.get("attendu",""))} "<br>'
                    f'<span class="tag">i</span> {safe_html(f.get("conseil",""))}'
                    '</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("Aucune faute detectee - bravo !")

        st.markdown(f"**Conseil general :** {pronunciation_result.get('conseil', '')}")
        st.markdown("</div>", unsafe_allow_html=True)


elif st.session_state.nav_page == "Quiz":
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag tag-red">04</span>Revision</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Quiz intelligent</h3></div>',
        unsafe_allow_html=True,
    )

    if st.session_state.quiz_question is None:
        if api_available():
            if st.button("Generer une question", key="new_quiz"):
                try:
                    with st.spinner("Preparation..."):
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

        answer = st.radio("Choisis une reponse", options, index=None, key="quiz_answer", label_visibility="collapsed")

        if st.button("Valider", key="validate_quiz"):
            if answer is None:
                st.warning("Choisis une reponse.")
            else:
                correct_index = int(q.get("bonne_reponse", 0))
                correct = options[correct_index] if options and correct_index < len(options) else ""
                if answer == correct:
                    st.success("Bonne reponse !")
                    st.session_state.score += 10
                    st.balloons()
                else:
                    st.error(f"Pas tout a fait. La bonne reponse etait : {correct}")
                st.info(q.get("explication", ""))
                st.session_state.questions_done += 1
                save_current_progress()

        if st.button("Nouvelle question", key="reset_quiz", on_click=reset_quiz):
            st.rerun()


elif st.session_state.nav_page == "Paramètres":
    st.markdown(
        '<div class="card"><span class="eyebrow">Paramètres</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Mon compte & préférences</h3>'
        '<p style="margin:0;font-size:.8rem;color:var(--muted)">Gère ton profil et l’apparence de FRANTSAY.</p></div>',
        unsafe_allow_html=True,
    )

    # --- 1. Profil & compte ---
    with st.expander("👤 Profil & compte", expanded=True):
        st.text_input("E-mail", value=st.session_state.user_email or "", disabled=True)
        new_pseudo = st.text_input(
            "Pseudo / nom affiché",
            value=st.session_state.user_pseudo or "",
            key="settings_pseudo_input",
            help="3 à 24 caractères : lettres, chiffres, points, tirets ou underscores.",
        )
        st.text_input("Niveau d'études", value=level, disabled=True)

        if st.button("Enregistrer le profil", key="save_profile_btn"):
            try:
                update_pseudo(st.session_state.user_id, new_pseudo)
                st.success("Profil mis à jour avec succès.")
            except Exception as exc:
                st.error(f"Impossible de mettre à jour le profil : {exc}")

    # --- 2. Apparence ---
    with st.expander("🌓 Apparence", expanded=False):
        theme_labels = {"auto": "Automatique (selon l'appareil)", "light": "Mode clair", "dark": "Mode sombre"}
        theme_keys = list(theme_labels.keys())
        current_choice = st.session_state.get("theme_mode", "auto")
        chosen_label = st.radio(
            "Thème de l'application",
            options=list(theme_labels.values()),
            index=theme_keys.index(current_choice) if current_choice in theme_keys else 0,
            key="theme_mode_radio",
        )
        chosen_key = theme_keys[list(theme_labels.values()).index(chosen_label)]
        if chosen_key != st.session_state.theme_mode:
            st.session_state.theme_mode = chosen_key
            save_current_progress()
            st.rerun()

    # --- 3. À propos ---
    with st.expander("ℹ️ À propos", expanded=False):
        st.markdown(
            f'<div style="font-size:.82rem;line-height:1.7;color:var(--ink)">'
            f'<b>{APP_NAME}</b><br>'
            f'<span style="color:var(--muted)">Plateforme d’apprentissage du français pour élèves et étudiants à Madagascar.</span><br>'
            f'<span style="color:var(--muted)">Auteur : RAKOTONIRINA Avosoa</span><br>'
            f'<span style="color:var(--muted)">© {datetime.now().year} RAKOTONIRINA Avosoa. Tous droits réservés.</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# =============================================================================
# 15. FOOTER
# =============================================================================

st.markdown(
    f'<div class="app-footer">© {datetime.now().year} RAKOTONIRINA Avosoa. Tous droits réservés.</div>',
    unsafe_allow_html=True,
)
