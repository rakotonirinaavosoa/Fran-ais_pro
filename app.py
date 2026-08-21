# -*- coding: utf-8 -*-
"""
FRANTSAY V3 — "L'AME DE MADAGASCAR"
Plateforme d'apprentissage du francais pour eleves et etudiants a Madagascar.
Stack: Streamlit + Supabase Auth (Email/MDP) + Gemini + gTTS
Design: Identite culturelle malgache subtile (Baobabs, Lemuriens, Aloalo)
Palette: Sable #FBF8F3, Terre rouge #B83A24, Ravinala #1B4D3E, Or Lamba #E69A2A
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
LEVELS = ["College", "Lycee", "Universite"]

st.set_page_config(
    page_title="FRANTSAY — Apprendre le francais",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# 2. PALETTE "L'AME DE MADAGASCAR" — Variables CSS
# =============================================================================

# Tanety = Terre rouge malgache
# Ravinala = Vert du palmier voyageur
# Lamba = Or des tissus traditionnels
# Raphia = Sable clair (fond principal)

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
}}
"""

# =============================================================================
# 3. SVG MASCOTTE LEMURIEN (style minimaliste, pas d'emoji)
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
# 4. CSS COMPLET — "L'AME DE MADAGASCAR"
# =============================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600&display=swap');
""" + ROOT_VARS + """

html, body, [class*="css"] { font-family: "Plus Jakarta Sans", "Inter", sans-serif; }
html { scroll-behavior: smooth; }
* { -webkit-tap-highlight-color: transparent; }

.stApp { background: var(--bg); color: var(--ink); transition: background-color .25s ease, color .25s ease; }

/* Texture subtile de fond style Lamba */
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23E69A2A' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
}

h1, h2, h3, h4, h5, p, span, label, div { color: var(--ink); }

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

/* CARTES */
.card, .lesson, .tip, .mini, .st-key-hero_box {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: 0 4px 14px -6px rgba(var(--shadow-rgb), 0.06);
    transition: transform .2s cubic-bezier(.16,1,.3,1), box-shadow .2s cubic-bezier(.16,1,.3,1),
                background-color .25s ease, border-color .25s ease;
    will-change: transform;
}

@media (hover: hover) and (pointer: fine) {
    .card:hover, .lesson:hover { transform: translateY(-2px); box-shadow: 0 12px 26px -10px rgba(var(--shadow-rgb),.14); border-color: var(--tanety); }
}
.card:active, .lesson:active { transform: scale(.985); }

.st-key-hero_box {
    padding: 1rem 1.1rem;
    margin-bottom: .7rem;
    background: linear-gradient(135deg, var(--card) 0%, var(--sable-chaud) 100%);
    overflow: hidden;
    position: relative;
}
.st-key-hero_box [data-testid="stVerticalBlockBorderWrapper"] { background: transparent; border: 0; }

/* SEPARATEURS ALOALO */
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

/* HERO */
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

/* ECRAN AUTH */
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

/* MASCOTTE LEMURIEN */
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

/* FORMULAIRE AUTH */
.auth-form-title { font-size: 1.25rem; font-weight: 800; letter-spacing: -.5px; margin-bottom: .2rem; }
.auth-form-subtitle { color: var(--muted); font-size: .78rem; margin-bottom: .8rem; }
.auth-side-card {
    background: linear-gradient(145deg, var(--card), var(--terre-clair));
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 1.35rem;
    box-shadow: 0 18px 45px rgba(var(--shadow-rgb), .08);
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

.identity-note {
    display: flex; gap: .7rem; align-items: center;
    padding: .85rem .95rem; margin-top: .7rem;
    border: 1px solid var(--line); background: var(--card);
    border-radius: 17px;
}
.identity-note-icon {
    width: 34px; height: 34px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    background: var(--terre-clair); color: var(--tanety); font-size: 1rem;
    flex-shrink: 0; /* empeche l'icone de se compresser si le texte est long */
}
/* Le conteneur texte doit lui-meme etre flex (colonne) pour que le gap
   du parent ne suffise pas a lui seul : titre et description ont besoin
   de leur propre espacement vertical, sinon ils se collent (bug corrige). */
.identity-note-text {
    display: flex;
    flex-direction: column;
    gap: .2rem;
}
.identity-note-text b { font-size: .74rem; color: var(--ink); }
.identity-note-text span { color: var(--muted); font-size: .68rem; line-height: 1.5; }

/* DASHBOARD */
.st-key-hero_box { background: transparent; border: 0; padding: 0; }
.dashboard-topline { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .3rem 0 1rem; }
.dashboard-topline .hero-title { margin: .25rem 0 .15rem; }
.wave { color: var(--tanety); }

.hero-user-badge {
    display: flex; align-items: center; gap: .65rem;
    padding: .55rem .7rem; border: 1px solid var(--line);
    background: var(--card); border-radius: 16px;
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
    background: var(--card); border: 1px solid var(--line);
    border-radius: 18px; padding: 1rem;
    box-shadow: 0 10px 25px rgba(var(--shadow-rgb), .045);
}
.dashboard-stat.accent {
    background: linear-gradient(135deg, var(--tanety), var(--terre-foncee));
    border-color: transparent;
}
.dashboard-stat span, .dashboard-stat small { display: block; }
.dashboard-stat span { color: var(--muted); font: 700 .55rem "JetBrains Mono"; letter-spacing: .7px; }
.dashboard-stat b { display: block; font-size: 1.25rem; letter-spacing: -.5px; margin: .28rem 0 .1rem; }
.dashboard-stat small { color: var(--muted); font-size: .58rem; }
.dashboard-stat.accent span, .dashboard-stat.accent b, .dashboard-stat.accent small { color: #fff; }

/* CARTES CONTENU */
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

/* GRILLE & LECONS */
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

/* Motif Aloalo subtil sur les lecons */
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

/* CAPSULES GRAMMATICALES */
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

/* PHRASE MODELE */
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

/* FAUTES PRONONCIATION */
.faute {
    border: 1px solid rgba(230,154,42,.3);
    background: var(--lamba-clair);
    border-radius: 12px;
    padding: .55rem .7rem;
    margin-bottom: .4rem;
    font-size: .8rem;
}
.faute .mot { font-weight: 800; color: var(--lamba-fonce); }

/* BOUTONS */
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

/* INPUTS */
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
    border-color: var(--tanety) !important;
    box-shadow: 0 0 0 3px var(--terre-clair) !important;
}

/* SELECTBOX DROPDOWN */
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

/* ONGLETS */
.stTabs [data-baseweb="tab-list"] {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: .3rem;
    background: var(--sable-chaud);
    padding: .3rem;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    justify-content: center;
    border-radius: 10px;
    padding: .4rem .3rem;
    font-weight: 700;
    font-size: .62rem;
    color: var(--muted);
    transition: background-color .2s cubic-bezier(.16,1,.3,1), color .2s ease, transform .15s ease;
}
.stTabs [aria-selected="true"] { background: var(--tanety) !important; color: white !important; }
@media (hover: hover) and (pointer: fine) {
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover { background: var(--sable-chaud); color: var(--tanety); }
}
.stTabs [data-baseweb="tab-panel"] { animation: tabFadeIn .25s ease; }
@keyframes tabFadeIn { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }

/* Icones onglets */
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
    color: var(--tanety);
    font-family: "JetBrains Mono", monospace;
    font-size: .52rem;
    font-weight: 800;
    border: 1px solid var(--line);
}
.stTabs [data-baseweb="tab-list"] button:nth-of-type(1) p::before { content: "H"; background: transparent; border-color: transparent; color: var(--tanety); font-size: .9rem; }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(2) p::before { content: "01"; color: var(--tanety); }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(3) p::before { content: "02"; color: var(--ravinala); }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(4) p::before { content: "03"; color: var(--lamba); }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(5) p::before { content: "04"; color: var(--terre-foncee); }
.stTabs [data-baseweb="tab-list"] button:nth-of-type(6) p::before { content: "05"; color: var(--muted); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"] p::before { background: rgba(255,255,255,.9); border-color: transparent; }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(1) p::before { color: #fff; background: transparent; }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(2) p::before { color: var(--tanety); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(3) p::before { color: var(--ravinala); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(4) p::before { color: var(--lamba); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(5) p::before { color: var(--terre-foncee); }
.stTabs [data-baseweb="tab-list"] [aria-selected="true"]:nth-of-type(6) p::before { color: var(--muted); }

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: var(--ravinala);
    border-right: 1px solid rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] * { color: #F7F4EC !important; }
section[data-testid="stSidebar"] .sidebar-section-label { color: #BFD0C8 !important; }
section[data-testid="stSidebar"] div.stButton > button {
    background: transparent !important;
    border: 1px solid rgba(230,154,42,.35) !important;
    color: #F6D18A !important;
    box-shadow: none !important;
    margin-top: 1rem;
}

.sidebar-brand { display: flex; align-items: center; gap: .55rem; padding: .15rem .1rem 1rem; }
.sidebar-brand .hero-lemur-svg { width: 38px; }
.sidebar-brand strong { display: block; font-size: 1rem; color: #fff; letter-spacing: -.3px; }
.sidebar-brand span { display: block; font-size: .55rem; color: #BFD0C8; margin-top: .08rem; }

.sidebar-profile {
    display: flex; align-items: center; gap: .6rem;
    padding: .7rem; border: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.045); border-radius: 15px;
    margin-bottom: 1rem;
}
.profile-avatar {
    width: 32px; height: 32px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, var(--tanety), var(--terre-foncee));
    color: #fff; font-weight: 800; font-size: .75rem;
}
.sidebar-profile b, .sidebar-profile span { display: block; }
.sidebar-profile b { font-size: .7rem; }
.sidebar-profile span { font-size: .56rem; color: #BFD0C8; }

.sidebar-section-label { color: #BFD0C8 !important; font: 700 .55rem "JetBrains Mono"; letter-spacing: 1px; margin: .85rem .15rem .35rem; }
.sidebar-nav-item {
    padding: .55rem .65rem; border-radius: 11px;
    color: #A8B2C4 !important; font-size: .68rem; font-weight: 600;
    margin: .12rem 0;
}
.sidebar-nav-item span { display: inline-flex; width: 21px; color: var(--lamba) !important; }
.sidebar-nav-item.active { color: #fff !important; background: linear-gradient(90deg, rgba(184,58,36,.95), rgba(139,46,26,.9)); box-shadow: 0 8px 20px rgba(184,58,36,.22); }
.sidebar-nav-item.active span { color: #fff !important; }

.sidebar-stats { display: grid; grid-template-columns: 1fr 1fr; gap: .45rem; margin-top: .8rem; }
.sidebar-stats div { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.07); border-radius: 13px; padding: .6rem; }
.sidebar-stats span { display: block; color: #BFD0C8 !important; font: 700 .48rem "JetBrains Mono"; }
.sidebar-stats b { display: block; color: #fff !important; font-size: .9rem; margin-top: .15rem; }

/* FOOTER */
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

/* CANAL AUDIO CACHE */
.st-key-audio_bridge_slot { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }

/* RESPONSIVE */
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
    .stTabs [data-baseweb="tab-list"] { grid-template-columns: repeat(3, 1fr); }
    .stTabs [data-baseweb="tab"] p { font-size: .58rem !important; }
}
@media (max-width: 480px) {
    .grid-2 { gap: .4rem; }
    .stTabs [data-baseweb="tab-list"] { grid-template-columns: repeat(3, 1fr); }
}

/* PROGRESS BAR PALIERS */
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

/* BADGE SCORE LAMBA */
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

/* PANNEAU DE DIAGNOSTIC CONFIGURATION (Supabase / secrets) */
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

/* ECRAN DE MAINTENANCE (remplace le panneau d'erreur technique) */
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
    ],
    "Lycee": [
        "Je pense que la lecture developpe l'imagination.",
        "Hier, nous avons visite le marche du village.",
        "Il faut reviser regulierement pour reussir ses examens.",
        "Mes amis et moi preparons un expose sur l'environnement.",
    ],
    "Universite": [
        "Cette recherche demontre l'importance de la rigueur scientifique.",
        "Le debat portait sur les consequences economiques de la decision.",
        "Il est essentiel d'analyser les sources avant de conclure.",
        "La cooperation internationale reste indispensable au developpement.",
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
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------------------------------------------------
# Lecture robuste des secrets : supporte a la fois la structure "plate"
#   SUPABASE_URL = "..."
# et la structure imbriquee (sections TOML) :
#   [supabase]
#   url = "..."
# Avec repli sur les variables d'environnement du systeme (utile en
# conteneur / Render / Railway ou les secrets ne passent pas par
# .streamlit/secrets.toml mais par de vraies env vars).
# -----------------------------------------------------------------------

# Alias de repli : cle plate -> [section][sous-cle] possibles
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
    """Essaie st.secrets[section][subkey] sans jamais lever d'exception."""
    try:
        section_obj = st.secrets.get(section)
        if section_obj is None:
            return ""
        value = section_obj.get(subkey) if hasattr(section_obj, "get") else section_obj[subkey]
        return str(value).strip() if value is not None else ""
    except Exception:
        return ""


def _secret(name: str, default: str = "") -> str:
    """
    Recherche une valeur de configuration dans cet ordre :
    1. st.secrets["NAME"]                (structure plate - recommandee)
    2. st.secrets["section"]["subkey"]   (structure imbriquee, ex: [supabase] url=...)
    3. os.environ["NAME"]                (vraies variables d'environnement)
    Ne leve jamais d'exception : renvoie `default` si rien n'est trouve.
    """
    # 1. Structure plate
    try:
        if name in st.secrets:
            value = str(st.secrets[name]).strip()
            if value:
                return value
    except Exception:
        pass

    # 2. Structure imbriquee (sections TOML)
    for section, subkey in _SECRET_ALIASES.get(name, []):
        value = _from_nested_secrets(section, subkey)
        if value:
            return value

    # 3. Variables d'environnement systeme
    env_value = os.environ.get(name, "").strip()
    if env_value:
        return env_value

    return default


@st.cache_resource(show_spinner=False)
def get_db_client() -> Client:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY manquant.")
    return create_client(url, key, options=ClientOptions(auto_refresh_token=False, persist_session=False))


def get_auth_client() -> Client:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL ou SUPABASE_ANON_KEY manquant.")
    return create_client(url, key, options=ClientOptions(auto_refresh_token=False, persist_session=False))


def get_cookie_controller() -> CookieController:
    return CookieController(key="frantsay_auth_cookie")


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


# Cles requises pour que l'app fonctionne, avec un libelle humain pour le
# panneau de diagnostic (jamais la valeur elle-meme n'est affichee).
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
        create_client(url, key, options=ClientOptions(auto_refresh_token=False, persist_session=False))
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
        create_client(url, key, options=ClientOptions(auto_refresh_token=False, persist_session=False))
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
    """Renvoie [(NOM, libelle, ok?, raison), ...] sans jamais exposer les valeurs."""
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
    # NOTE : .select() n'existe pas sur l'objet retourne par .insert() en
    # supabase-py (contrairement a supabase-js). .execute() renvoie deja la
    # ligne inseree dans .data grace au header "Prefer: return=representation"
    # que la librairie ajoute par defaut sur insert() -- inutile de le
    # rappeler explicitement.
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
    get_cookie_controller().set(
        SESSION_COOKIE_NAME, session_id,
        key="set_frantsay_sid", path="/",
        max_age=SESSION_MAX_AGE, secure=True, same_site="strict"
    )


def delete_login_session(session_id: str | None) -> None:
    if not session_id:
        return
    try:
        get_db_client().table("app_sessions").delete().eq("session_id_hash", _hash_sid(session_id)).execute()
    finally:
        try:
            get_cookie_controller().delete(SESSION_COOKIE_NAME, key="delete_frantsay_sid")
        except Exception:
            pass


def restore_from_cookie() -> bool:
    try:
        sid = get_cookie_controller().get(SESSION_COOKIE_NAME)
        if not sid or not isinstance(sid, str):
            return False
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
    return {"score": int(st.session_state.score), "questions_done": int(st.session_state.questions_done)}


def save_progress(user_id: str, data: dict[str, Any]) -> None:
    if not user_id:
        raise ValueError("user_id manquant.")
    score = max(0, int(data.get("score", 0)))
    done = max(0, int(data.get("questions_done", 0)))
    get_db_client().table("users").update({
        "score": score,
        "questions_done": done,
        "progress": {"score": score, "questions_done": done},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", user_id).execute()


def save_current_progress() -> None:
    if not st.session_state.get("identified") or not st.session_state.get("user_id"):
        return
    try:
        save_progress(st.session_state.user_id, current_progress())
    except Exception as exc:
        st.warning(f"La progression n'a pas pu etre synchronisee : {exc}")


def logout_user() -> None:
    sid = get_cookie_controller().get(SESSION_COOKIE_NAME)
    delete_login_session(sid)
    st.session_state.clear()
    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value
    st.session_state.model_sentence = random.choice(MODEL_SENTENCES["Lycee"])


# Tentative de restauration automatique au chargement
if not st.session_state.identified:
    restore_from_cookie()

# =============================================================================
# 8. ECRAN D'AUTHENTIFICATION
# =============================================================================

def render_auth_screen() -> None:
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
                    <div class="auth-feature-grid">
                        <div class="auth-feature">
                            <div class="feature-icon">01</div>
                            <b>Apprentissage</b>
                            <span>Lecons adaptees</span>
                        </div>
                        <div class="auth-feature">
                            <div class="feature-icon green">02</div>
                            <b>Missions</b>
                            <span>Situations utiles</span>
                        </div>
                        <div class="auth-feature">
                            <div class="feature-icon amber">03</div>
                            <b>Prononciation</b>
                            <span>Travail de l'oral</span>
                        </div>
                        <div class="auth-feature">
                            <div class="feature-icon red">04</div>
                            <b>Quiz</b>
                            <span>Defis rapides</span>
                        </div>
                    </div>
                </div>
                <div class="auth-panel">
                    <div class="auth-panel-top">
                        <div>
                            <div class="auth-welcome">Bienvenue !</div>
                            <div class="auth-welcome-sub">Ton espace d'apprentissage t'attend.</div>
                        </div>
                        <div class="secure-pill">
                            <span class="secure-dot"></span> Connexion securisee
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
            with st.expander("🔧 Diagnostic technique (visible uniquement avec le code admin)", expanded=True):
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

        tabs = st.tabs(["Connexion", "Creer un compte"])

        with tabs[0]:
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

        with tabs[1]:
            with st.form("registration_form"):
                email_input = st.text_input("E-mail", autocomplete="email", placeholder="exemple@email.com")
                pseudo_input = st.text_input("Pseudo (facultatif)", autocomplete="username", placeholder="Visible uniquement dans ton profil prive")
                password_input = st.text_input("Mot de passe", type="password", autocomplete="new-password")
                confirm_input = st.text_input("Confirmer le mot de passe", type="password", autocomplete="new-password")
                level_input = st.radio("Ton niveau d'etudes", LEVELS, horizontal=True)
                submitted = st.form_submit_button("Creer mon compte", use_container_width=True)

            if submitted:
                try:
                    with st.spinner("Creation de ton espace..."):
                        message = sign_up(
                            email_input or "",
                            password_input or "",
                            confirm_input or "",
                            pseudo_input or "",
                            level_input,
                        )
                    if st.session_state.get("identified"):
                        st.rerun()
                    st.success(message)
                except Exception as exc:
                    st.error(str(exc))

    with col_right:
        st.markdown(
            '<div class="auth-side-card">'
            '<div class="side-card-icon">+</div>'
            '<div class="side-card-title">Ton parcours reste prive.</div>'
            '<p>Ton adresse e-mail et ton pseudo ne sont jamais affiches sur les pages publiques de FRANTSAY.</p>'
            '<div class="side-check"><span>✓</span> Infrastructure de securite avancee et chiffree</div>'
            '<div class="side-check"><span>✓</span> Sauvegarde automatique et synchronisation en temps reel</div>'
            '<div class="side-check"><span>✓</span> Configuration fixe du parcours d\'apprentissage</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="identity-note">'
            '<div class="identity-note-icon" aria-hidden="true">i</div>'
            '<div class="identity-note-text">'
            '<b>Confidentialite</b>'
            '<span>Tes donnees restent entre toi et toi. Aucun e-mail affiche publiquement.</span>'
            '</div>'
            '</div>',
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
# 10. APPELS API GEMINI
# =============================================================================

def get_api_key() -> str:
    return _secret("GEMINI_API_KEY")


def api_available() -> bool:
    return bool(get_api_key())


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
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=schema_class,
        ),
    )
    return json.loads(response.text)


def call_gemini_text(system_prompt: str, user_prompt: str) -> str:
    key = get_api_key()
    if not key:
        raise ValueError("Cle API Gemini manquante cote serveur (st.secrets).")
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
        '<div class="tip"><span class="tag tag-amber">ATT</span> '
        "Les administrateurs sont en train d'activer l'IA, patientez s'il vous plait. "
        "En attendant, les fiches de l'onglet Accueil restent consultables sans IA.</div>",
        unsafe_allow_html=True,
    )

# =============================================================================
# 11. PROMPTS SYSTEME (ADAPTES AU NIVEAU VERROUILLE)
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


# =============================================================================
# 12. ENREGISTREUR WEB AUDIO NATIF
# =============================================================================

RECORDER_HTML_TEMPLATE = """
<div id="rec-wrap">
  <div class="rec-row">
    <button id="btnStart" class="rec-btn rec-start" type="button">[o] Demarrer</button>
    <button id="btnStop" class="rec-btn rec-stop" type="button" disabled>[x] Arreter</button>
  </div>
  <div class="rec-meta">
    <span id="recDot" class="rec-dot"></span>
    <span id="recStatus" class="rec-status">Pret a enregistrer</span>
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
  .rec-start { background: __TANETY__; color: #fff; box-shadow: 0 4px 12px rgba(184,58,36,.28); }
  .rec-stop { background: __TERRE_FONCEE__; color: #fff; box-shadow: 0 4px 12px rgba(139,46,26,.28); }
  .rec-meta {
    display: flex; align-items: center; gap: 8px;
    font-size: 12px; color: __MUTED__; padding: 2px 2px;
  }
  .rec-dot {
    width: 8px; height: 8px; border-radius: 50%; background: __LINE__; flex: none;
  }
  .rec-dot.live { background: __TANETY__; box-shadow: 0 0 0 0 rgba(184,58,36,.6); animation: pulse 1.1s infinite; }
  @keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(184,58,36,.55); }
    70% { box-shadow: 0 0 0 8px rgba(184,58,36,0); }
    100% { box-shadow: 0 0 0 0 rgba(184,58,36,0); }
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
      setStatus('Analyse envoyee - resultat ci-dessous.', false);
    } catch (err) {
      setStatus('Echec de transmission : ' + err.message, false);
    }
  }

  async function onRecordingStop() {
    try {
      setStatus('Traitement de l\'enregistrement...', false);
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
      setStatus('Micro refuse ou indisponible.', false);
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
    setStatus('Traitement de l\'enregistrement...', false);
  }

  btnStart.addEventListener('click', startRecording);
  btnStop.addEventListener('click', stopRecording);
})();
</script>
"""


def build_recorder_html(t: dict) -> str:
    return (
        RECORDER_HTML_TEMPLATE
        .replace("__CARD__", t["card"])
        .replace("__TANETY__", t["tanety"])
        .replace("__TERRE_FONCEE__", t["terre_foncee"])
        .replace("__MUTED__", t["muted"])
        .replace("__LINE__", t["line"])
        .replace("__INK__", t["ink"])
    )

# =============================================================================
# 13. SIDEBAR — Navigation du tableau de bord
# =============================================================================

with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand">{LEMUR_SVG}<div><strong>FRANTSAY</strong><span>Ton parcours de francais</span></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-profile">'
        '<div class="profile-avatar">' + safe_html((st.session_state.user_pseudo or "F")[:1].upper()) + '</div>'
        '<div><b>Profil prive</b><span>' + safe_html(st.session_state.level) + '</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Profil prive", expanded=False):
        st.caption("Ces informations ne sont pas affichees sur l'accueil.")
        st.write(f"E-mail : {st.session_state.user_email}")
        if st.session_state.user_pseudo:
            st.write(f"Pseudo : {st.session_state.user_pseudo}")
        st.write(f"Niveau verrouille : {st.session_state.level}")

    st.markdown('<div class="sidebar-section-label">TON ESPACE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item active"><span>H</span> Tableau de bord</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>G</span> Grammaire</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>M</span> Missions</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>P</span> Prononciation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-item"><span>Q</span> Quiz</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">PARCOURS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-nav-item"><span>LOCK</span> Niveau verrouille : '
        + safe_html(st.session_state.level) + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-stats">'
        '<div><span>POINTS</span><b>' + str(st.session_state.score) + '</b></div>'
        '<div><span>ACTIVITES</span><b>' + str(st.session_state.questions_done) + '</b></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("Se deconnecter", key="logout_button", use_container_width=True):
        logout_user()
        st.rerun()


# =============================================================================
# 14. EN-TETE — Hero compact avec mascotte lemurien
# =============================================================================

status = (
    '<span class="badge badge-ok"><span class="dot"></span>Assistant IA actif</span>'
    if api_available()
    else '<span class="badge badge-warn">Cours disponibles - IA non activee</span>'
)

with st.container(key="hero_box"):
    st.markdown(
        f"""<div class="dashboard-topline"><div>
            <div class="eyebrow"><span class="tag tag-solid">FRANTSAY</span> TABLEAU DE BORD</div>
            <h1 class="hero-title">Ton espace d'apprentissage <span class="wave">*</span></h1>
            <p class="hero-sub">Pret a continuer ton apprentissage ? - Parcours {safe_html(level)}</p>
        </div>
        <div class="hero-user-badge">
            <span class="hero-avatar">FR</span>
            <div><b>Profil prive</b><span>Niveau verrouille</span></div>
        </div></div>
        <div class="dashboard-stat-grid">
            <div class="dashboard-stat">
                <span>PROGRESSION</span>
                <b>{min(100, max(0, st.session_state.score))}%</b>
                <small>Continue comme ca</small>
            </div>
            <div class="dashboard-stat">
                <span>POINTS</span>
                <b>{st.session_state.score:,}</b>
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

components.html(LEMUR_CLICK_JS, height=0)


# =============================================================================
# 15. ONGLETS ET MODULES
# =============================================================================

tab_home, tab_defis, tab_correction, tab_missions, tab_pron, tab_quiz = st.tabs(
    ["Accueil", "Defis", "Grammaire", "Missions", "Prononciation", "Quiz"]
)


# --- ONGLET : ACCUEIL / PARCOURS ---
with tab_home:
    st.markdown(
        '<div class="card"><span class="eyebrow">Parcours recommande</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Apprendre sans se perdre</h3>'
        '<p style="margin:0;font-size:.8rem;color:var(--muted)">Lis une lecon, ecoute les exemples, '
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
            f'<span style="font-size:.72rem;color:var(--tanety);font-weight:700">Ex : {safe_html(lesson["exemple"])}</span>'
            '</div>'
        )
    grid_html = '<div class="grid-2">' + "".join(cards) + "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)


# --- ONGLET : DEFIS (parcours de paliers) ---
with tab_defis:
    score = st.session_state.score
    st.markdown(
        '<div class="card"><span class="eyebrow">Progression</span>'
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


# --- ONGLET 01 : CORRECTION GRAMMATICALE ---
with tab_correction:
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

# --- ONGLET 02 : MISSIONS ---
with tab_missions:
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


# --- ONGLET 03 : PRONONCIATION INTERACTIVE ---
with tab_pron:
    st.markdown(
        '<div class="card"><span class="eyebrow"><span class="tag tag-amber">03</span>Prononciation interactive</span>'
        '<h3 style="margin:.2rem 0;font-size:1rem">Entraine ta prononciation</h3></div>',
        unsafe_allow_html=True,
    )

    # Phrase modele + TTS
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("[R] Nouvelle phrase", key="new_sentence"):
            st.session_state.model_sentence = random.choice(MODEL_SENTENCES[level])
            st.session_state.pronunciation_result = None
    with colB:
        listen_model = st.button("[P] Ecouter le modele", key="listen_model")

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

    # Enregistreur natif
    st.markdown(
        '<div class="card"><span class="eyebrow">A toi de parler</span>'
        '<h4 style="margin:.2rem 0;font-size:.95rem">Enregistre-toi</h4>'
        '<p style="margin:0;font-size:.76rem;color:var(--muted)">'
        "Appuie sur 'Demarrer', lis la phrase a voix haute, puis appuie sur 'Arreter'. "
        "L'analyse demarre automatiquement.</p></div>",
        unsafe_allow_html=True,
    )

    with st.container(key="audio_bridge_slot"):
        audio_data_url = st.text_input(
            "audio_channel",
            key="audio_channel_value",
            label_visibility="collapsed",
        )

    components.html(build_recorder_html(THEME), height=110, scrolling=False)

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
                                PRONONCIATION_PROMPT,
                                audio_bytes,
                                mime_type,
                                f"Phrase modele attendue : {st.session_state.model_sentence}",
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


# --- ONGLET 04 : QUIZ ---
with tab_quiz:
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

        if st.button("Nouvelle question", key="reset_quiz"):
            st.session_state.quiz_question = None
            st.session_state.quiz_answer = None
            st.rerun()


# =============================================================================
# 16. FOOTER
# =============================================================================

st.markdown(
    '<div class="app-footer"><b>FRANTSAY</b>&nbsp;-&nbsp;Concu par RAKOTONIRINA Avosoa</div>',
    unsafe_allow_html=True,
)
