# -*- coding: utf-8 -*-
"""
=====================================================================================
 FRANTSAY
 Plateforme d'apprentissage du français pour les élèves et étudiants à Madagascar.

 Stack : Streamlit + Google Gemini (SDK google-genai, avec repli automatique sur
 l'ancien SDK google-generativeai si nécessaire) + gTTS
=====================================================================================
"""

import streamlit as st
import json
import re
import io
import os
import datetime

# =====================================================================================
# 1. CONSTANTES DE CONFIGURATION
# =====================================================================================

ADMIN_EMAIL = "admin@frantsay.mg"
FICHIER_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frantsay_config.json")
NIVEAUX = ["Collège", "Lycée", "Université"]
NOM_MODELE_GEMINI = "gemini-2.0-flash"

# =====================================================================================
# 2. CONFIGURATION DE LA PAGE
# =====================================================================================

st.set_page_config(
    page_title="FRANTSAY",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================================
# 3. CSS PERSONNALISÉ — STYLE EDTECH SOMBRE
# =====================================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(6, 182, 212, 0.10) 0%, transparent 45%),
        radial-gradient(circle at 85% 100%, rgba(6, 182, 212, 0.08) 0%, transparent 45%),
        #0F172A;
    color: #E2E8F0;
}

h1, h2, h3, h4, h5, p, span, label, div {
    color: #E2E8F0;
}

/* En-tête */
.frantsay-header {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.85) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(6, 182, 212, 0.35);
    border-radius: 20px;
    padding: 2.6rem 2.8rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 0 40px rgba(6, 182, 212, 0.08), 0 8px 24px rgba(0, 0, 0, 0.35);
}
.frantsay-header .marque {
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: -1px;
    margin: 0;
    background: linear-gradient(90deg, #06B6D4, #67E8F9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.frantsay-header p {
    color: #94A3B8;
    font-size: 1.02rem;
    margin-top: 0.7rem;
    max-width: 760px;
    line-height: 1.6;
}
.frantsay-meta {
    display: inline-block;
    background: rgba(6, 182, 212, 0.12);
    color: #67E8F9;
    border: 1px solid rgba(6, 182, 212, 0.35);
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 1rem;
    margin-right: 0.5rem;
}

/* Cartes en verre */
.frantsay-card {
    background: rgba(30, 41, 59, 0.65);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.28);
    margin-bottom: 1.2rem;
    transition: border-color 0.2s ease-in-out;
}
.frantsay-card:hover {
    border-color: rgba(6, 182, 212, 0.4);
}
.frantsay-card h4 {
    margin-top: 0;
    font-weight: 800;
    color: #F1F5F9;
}
.frantsay-label {
    display: inline-block;
    background: rgba(6, 182, 212, 0.14);
    color: #22D3EE;
    border: 1px solid rgba(6, 182, 212, 0.4);
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}

/* Carte d'accueil / configuration stylisée */
.frantsay-config-card {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.14) 0%, rgba(30, 41, 59, 0.75) 60%);
    border: 1px solid rgba(6, 182, 212, 0.4);
    border-radius: 18px;
    padding: 2rem 2.2rem;
    text-align: center;
    margin-bottom: 1.4rem;
    box-shadow: 0 0 32px rgba(6, 182, 212, 0.10);
}
.frantsay-config-card h4 {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}
.frantsay-config-card p {
    color: #94A3B8;
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.6;
}

/* Badges de décomposition grammaticale */
.badge-groupe {
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    border-radius: 12px;
    padding: 0.6rem 1rem;
    margin: 0.3rem 0.45rem 0.3rem 0;
    min-width: 120px;
    border: 1px solid transparent;
}
.badge-groupe .badge-type {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.85;
}
.badge-groupe .badge-texte {
    font-size: 1.02rem;
    font-weight: 700;
    margin-top: 0.2rem;
}
.badge-sujet {
    background: rgba(6, 182, 212, 0.14);
    border-color: rgba(6, 182, 212, 0.45);
    color: #22D3EE;
    box-shadow: 0 0 14px rgba(6, 182, 212, 0.12);
}
.badge-verbe {
    background: rgba(52, 211, 153, 0.14);
    border-color: rgba(52, 211, 153, 0.45);
    color: #34D399;
    box-shadow: 0 0 14px rgba(52, 211, 153, 0.12);
}
.badge-complement {
    background: rgba(244, 114, 182, 0.14);
    border-color: rgba(244, 114, 182, 0.45);
    color: #F472B6;
    box-shadow: 0 0 14px rgba(244, 114, 182, 0.12);
}
.badge-autre {
    background: rgba(148, 163, 184, 0.14);
    border-color: rgba(148, 163, 184, 0.4);
    color: #CBD5E1;
}

/* Écran de connexion */
.login-wrapper {
    max-width: 470px;
    margin: 4rem auto;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(6, 182, 212, 0.35);
    border-radius: 20px;
    padding: 2.8rem 2.6rem;
    box-shadow: 0 0 50px rgba(6, 182, 212, 0.10), 0 10px 30px rgba(0, 0, 0, 0.4);
    text-align: center;
}
.login-wrapper h1 {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: -1px;
    margin-bottom: 0.3rem;
    background: linear-gradient(90deg, #06B6D4, #67E8F9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.login-wrapper p {
    color: #94A3B8;
    font-size: 0.96rem;
    margin-bottom: 1.8rem;
}

/* Champs de saisie */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    background-color: rgba(15, 23, 42, 0.6) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(148, 163, 184, 0.25) !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #06B6D4 !important;
    box-shadow: 0 0 0 1px #06B6D4 !important;
}

/* Boutons avec effet lumineux */
div.stButton > button {
    background: linear-gradient(90deg, #06B6D4, #0891B2);
    color: #F0FDFF;
    font-weight: 700;
    border-radius: 12px;
    border: none;
    padding: 0.65rem 1.6rem;
    box-shadow: 0 0 0 rgba(6, 182, 212, 0);
    transition: all 0.22s ease-in-out;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 22px rgba(6, 182, 212, 0.55), 0 8px 20px rgba(0, 0, 0, 0.3);
    background: linear-gradient(90deg, #22D3EE, #06B6D4);
}

/* Onglets */
button[data-baseweb="tab"] {
    font-weight: 700;
    font-size: 0.98rem;
    color: #94A3B8 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #22D3EE !important;
}
div[data-baseweb="tab-highlight"] {
    background-color: #06B6D4 !important;
}

section[data-testid="stSidebar"] {
    background: #0B1220;
    border-right: 1px solid rgba(6, 182, 212, 0.18);
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1;
}

.frantsay-footer {
    text-align: center;
    color: #475569;
    font-size: 0.8rem;
    padding: 1.8rem 0 0.6rem 0;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# =====================================================================================
# 4. PERSISTANCE DE LA CONFIGURATION GLOBALE (CLÉ API PARTAGÉE)
# =====================================================================================


def charger_config() -> dict:
    """Charge la configuration globale (clé API Gemini) depuis le fichier local."""
    if not os.path.exists(FICHIER_CONFIG):
        return {"gemini_api_key": ""}
    try:
        with open(FICHIER_CONFIG, "r", encoding="utf-8") as f:
            contenu = json.load(f)
            if "gemini_api_key" not in contenu:
                contenu["gemini_api_key"] = ""
            return contenu
    except Exception:
        return {"gemini_api_key": ""}


def sauvegarder_config(cle_api: str) -> None:
    """Enregistre la clé API Gemini de façon globale pour tous les utilisateurs."""
    with open(FICHIER_CONFIG, "w", encoding="utf-8") as f:
        json.dump({"gemini_api_key": cle_api}, f)


def cle_api_disponible() -> bool:
    """Indique si une clé API Gemini est actuellement configurée."""
    return bool(st.session_state.config_globale.get("gemini_api_key", "").strip())


def afficher_carte_configuration_absente() -> None:
    """Affiche une carte stylisée (au lieu d'une erreur brute) quand la clé API manque."""
    if st.session_state.role_utilisateur == "admin":
        st.markdown(
            """
            <div class="frantsay-config-card">
                <h4>Activation de la plateforme requise</h4>
                <p>Aucune clé API Gemini n'est encore enregistrée. Rends-toi dans
                l'onglet "Configuration Admin" pour l'ajouter et activer toutes les
                fonctionnalités intelligentes pour l'ensemble des utilisateurs.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="frantsay-config-card">
                <h4>Plateforme en cours d'activation</h4>
                <p>Ton espace d'apprentissage est presque prêt. L'administrateur
                finalise la configuration de la plateforme. Reviens dans quelques
                instants pour profiter de toutes les fonctionnalités.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================================================
# 5. PROMPTS SYSTÈME EMBARQUÉS
# =====================================================================================

SYSTEM_PROMPT_CORRECTION = """
Tu es un professeur de français expert en didactique du Français Langue Étrangère,
spécialisé dans l'accompagnement des apprenants malgaches (Madagascar).

CONTEXTE SUR LES APPRENANTS :
Les élèves malgaches rencontrent des difficultés récurrentes dues à des interférences
avec leur langue maternelle, le malagasy :
1. Structure de phrase : en malagasy, l'ordre habituel est Verbe-Objet-Sujet, ce qui
   provoque des inversions du type "Mange Rakoto du riz" au lieu de
   "Rakoto mange du riz".
2. Absence de genre grammatical : le malagasy ne marque pas le masculin/féminin, d'où
   des confusions fréquentes sur "le/la", "un/une", "mon/ma", les accords d'adjectifs.
3. Système verbal différent : le malagasy exprime le temps par des préfixes, ce qui
   complique l'apprentissage des temps français (présent, passé composé, imparfait,
   futur, subjonctif).
4. Prononciation : difficultés sur les sons u/ou, b/v, p/f, et les voyelles nasales
   (an, en, on, in).

TA MISSION :
Analyser la phrase ou le texte fourni par l'élève et répondre UNIQUEMENT avec un objet
JSON valide, sans aucun texte avant ou après, sans balises de code, respectant
exactement cette structure :

{
  "phrase_corrigee": "la phrase corrigée, naturelle et complète",
  "decomposition": [
    {"type": "Sujet", "texte": "..."},
    {"type": "Verbe", "texte": "..."},
    {"type": "Complément", "texte": "..."}
  ],
  "explication": "explication pédagogique simple et bienveillante de la règle
                   concernée, en faisant le lien avec le malagasy si l'erreur en
                   vient probablement",
  "conseil_prononciation": "conseil concret sur les mots de la phrase corrigée qui
                             sont difficiles à prononcer pour un malgachophone"
}

RÈGLES :
- Le champ "type" de chaque élément de "decomposition" doit être : "Sujet", "Verbe",
  "Complément" ou "Autre". Décompose l'intégralité de la phrase corrigée, groupe par
  groupe, dans l'ordre naturel de la phrase.
- Si la phrase de l'élève était déjà correcte, indique-le dans "explication" et
  propose éventuellement une variante plus riche dans "phrase_corrigee".
- Adapte le niveau de vocabulaire de "explication" au niveau scolaire indiqué par
  l'utilisateur.
- Le ton doit être chaleureux, encourageant, jamais condescendant.
- Réponds toujours en français, uniquement avec le JSON demandé.
"""

SYSTEM_PROMPT_DIALOGUE = """
Tu es un professeur de français qui conçoit des dialogues pédagogiques pour des
apprenants malgaches, dans un cadre académique ou professionnel.

Ta mission : générer un court dialogue réaliste en français (6 à 10 répliques),
mettant en scène une situation du quotidien académique ou professionnel à
Madagascar (école, université, entretien, administration, vie de bureau...).

CONSIGNES :
- Utilise des prénoms malgaches courants et éventuellement des lieux locaux.
- Adapte le niveau de langue au niveau scolaire indiqué (Collège : phrases simples ;
  Lycée : phrases plus riches ; Université : registre soutenu, vocabulaire
  professionnel).
- Structure ta réponse en Markdown avec des titres sobres, sans emoji :
  "Dialogue", "Vocabulaire à retenir" (4 à 6 mots ou expressions expliqués
  simplement), "Point de grammaire" (une règle illustrée dans le dialogue, avec le
  lien vers les erreurs typiques dues au malagasy si pertinent).
- Réponds toujours en français.
"""

# =====================================================================================
# 6. SONS DIFFICILES (ATELIER DE PRONONCIATION)
# =====================================================================================

SONS_DIFFICILES = [
    {
        "titre": "Le son [u] et le son [ou]",
        "explication": (
            "En malagasy, l'opposition entre le [u] français (comme dans « lune ») "
            "et le [ou] français (comme dans « joue ») n'existe pas de la même "
            "manière, d'où une confusion fréquente. Pour le [u], arrondissez "
            "fortement les lèvres et avancez la langue. Pour le [ou], arrondissez "
            "aussi les lèvres mais reculez la langue vers l'arrière de la bouche."
        ),
        "paires": [("tu", "tout"), ("rue", "roue"), ("dessus", "dessous"), ("pull", "poule")],
    },
    {
        "titre": "Le son [b] et le son [v]",
        "explication": (
            "Le [b] est une consonne occlusive : les lèvres se ferment puis "
            "s'ouvrent d'un coup. Le [v] est une consonne fricative continue : les "
            "dents du haut touchent légèrement la lèvre inférieure et l'air passe "
            "en vibrant. Beaucoup d'apprenants prononcent le [v] comme un [b] par "
            "habitude. Entraînez-vous à faire vibrer l'air en continu pour le [v]."
        ),
        "paires": [("bas", "vas"), ("bœuf", "veuf"), ("bin", "vin"), ("bous", "vous")],
    },
    {
        "titre": "Le son [p] et le son [f]",
        "explication": (
            "Le [p] est occlusif (les lèvres se ferment puis explosent), le [f] "
            "est fricatif continu (l'air passe entre les dents du haut et la "
            "lèvre du bas). Placez la main devant la bouche : pour le [p], vous "
            "devez sentir un souffle bref et sec ; pour le [f], un souffle long "
            "et continu."
        ),
        "paires": [("pou", "fou"), ("pin", "fin"), ("panne", "fane"), ("port", "fort")],
    },
    {
        "titre": "Les voyelles nasales (an, en, on, in)",
        "explication": (
            "Le français possède des voyelles nasales qui n'existent pas telles "
            "quelles en malagasy : l'air passe à la fois par la bouche et par le "
            "nez. Beaucoup d'apprenants ajoutent un « n » ou un « ng » marqué "
            "après la voyelle au lieu de nasaliser la voyelle elle-même. "
            "Entraînez-vous en pinçant légèrement le nez : si le son change "
            "beaucoup, c'est que la nasalisation est bien réalisée."
        ),
        "paires": [("bon", "banc"), ("vin", "vent"), ("son", "sang"), ("pain", "pont")],
    },
]

SCENARIOS = [
    "Un exposé oral devant la classe",
    "Un entretien d'embauche pour un premier emploi",
    "Une réunion de travail en entreprise",
    "Une inscription à l'université",
    "Un rendez-vous dans une administration",
    "Un échange avec un professeur après un cours",
]

# =====================================================================================
# 7. FONCTIONS D'ACCÈS À GEMINI ET À LA SYNTHÈSE VOCALE
# =====================================================================================


def appeler_gemini(system_prompt: str, user_prompt: str) -> str:
    """
    Appelle Google Gemini avec la clé globale configurée par l'administrateur.
    Utilise en priorité le SDK récent `google-genai`. Si celui-ci n'est pas
    installé, bascule automatiquement sur l'ancien SDK `google-generativeai`
    pour garantir la compatibilité.
    """
    cle_api = st.session_state.config_globale.get("gemini_api_key", "")
    if not cle_api:
        raise ValueError("Aucune clé API Gemini n'est configurée pour le moment.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=cle_api)
        reponse = client.models.generate_content(
            model=NOM_MODELE_GEMINI,
            contents=user_prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return reponse.text

    except ImportError:
        import google.generativeai as genai_legacy

        genai_legacy.configure(api_key=cle_api)
        modele = genai_legacy.GenerativeModel(
            model_name=NOM_MODELE_GEMINI,
            system_instruction=system_prompt,
        )
        reponse = modele.generate_content(user_prompt)
        return reponse.text


def extraire_json(texte: str) -> dict:
    """Nettoie et parse une réponse JSON éventuellement entourée de balises de code."""
    nettoye = texte.strip()
    nettoye = re.sub(r"^```(json)?", "", nettoye).strip()
    nettoye = re.sub(r"```$", "", nettoye).strip()
    return json.loads(nettoye)


def generer_audio(texte: str, lent: bool = False) -> io.BytesIO:
    """Génère un fichier audio MP3 en français à partir d'un texte via gTTS."""
    from gtts import gTTS

    tts = gTTS(text=texte, lang="fr", slow=lent)
    tampon = io.BytesIO()
    tts.write_to_fp(tampon)
    tampon.seek(0)
    return tampon


# =====================================================================================
# 8. INITIALISATION DE L'ÉTAT DE SESSION
# =====================================================================================

if "authentifie" not in st.session_state:
    st.session_state.authentifie = False

if "email_utilisateur" not in st.session_state:
    st.session_state.email_utilisateur = ""

if "role_utilisateur" not in st.session_state:
    st.session_state.role_utilisateur = "eleve"

if "niveau" not in st.session_state:
    st.session_state.niveau = "Lycée"

if "config_globale" not in st.session_state:
    st.session_state.config_globale = charger_config()

if "historique_corrections" not in st.session_state:
    st.session_state.historique_corrections = []

if "historique_dialogues" not in st.session_state:
    st.session_state.historique_dialogues = []

# =====================================================================================
# 9. ÉCRAN DE CONNEXION
# =====================================================================================

REGEX_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

if not st.session_state.authentifie:
    st.markdown(
        """
        <div class="login-wrapper">
            <h1>FRANTSAY</h1>
            <p>Plateforme d'apprentissage du français pour les élèves et
            étudiants à Madagascar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    colonne_gauche, colonne_centre, colonne_droite = st.columns([1, 1.4, 1])
    with colonne_centre:
        email_saisi = st.text_input("Adresse e-mail", placeholder="prenom.nom@exemple.mg")
        if st.button("Se connecter", use_container_width=True):
            if not email_saisi or not re.match(REGEX_EMAIL, email_saisi.strip()):
                st.error("Merci de saisir une adresse e-mail valide.")
            else:
                st.session_state.authentifie = True
                st.session_state.email_utilisateur = email_saisi.strip()
                if email_saisi.strip().lower() == ADMIN_EMAIL.lower():
                    st.session_state.role_utilisateur = "admin"
                else:
                    st.session_state.role_utilisateur = "eleve"
                st.rerun()

    st.stop()

# =====================================================================================
# 10. BARRE LATÉRALE (APRÈS CONNEXION)
# =====================================================================================

with st.sidebar:
    st.markdown("### Session")
    st.markdown(f"**Connecté en tant que**  \n{st.session_state.email_utilisateur}")
    libelle_role = "Administrateur" if st.session_state.role_utilisateur == "admin" else "Élève"
    st.markdown(f"**Rôle**  \n{libelle_role}")

    st.divider()

    niveau_choisi = st.selectbox(
        "Niveau d'études",
        options=NIVEAUX,
        index=NIVEAUX.index(st.session_state.niveau),
    )
    st.session_state.niveau = niveau_choisi

    st.divider()

    if st.button("Se déconnecter", use_container_width=True):
        st.session_state.authentifie = False
        st.session_state.email_utilisateur = ""
        st.session_state.role_utilisateur = "eleve"
        st.rerun()

# =====================================================================================
# 11. EN-TÊTE PRINCIPAL
# =====================================================================================

st.markdown(
    f"""
    <div class="frantsay-header">
        <p class="marque">FRANTSAY</p>
        <p>Une plateforme pensée pour accompagner les élèves et étudiants malgaches
        dans l'apprentissage du français, en tenant compte des spécificités
        linguistiques du malagasy.</p>
        <span class="frantsay-meta">Niveau : {st.session_state.niveau}</span>
        <span class="frantsay-meta">{datetime.date.today().strftime('%d/%m/%Y')}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if not cle_api_disponible():
    afficher_carte_configuration_absente()

# =====================================================================================
# 12. ONGLETS PRINCIPAUX
# =====================================================================================

if st.session_state.role_utilisateur == "admin":
    onglet_correction, onglet_prononciation, onglet_pratique, onglet_admin = st.tabs(
        ["Structure & Correction", "Atelier de Prononciation", "Pratique Guidée", "Configuration Admin"]
    )
else:
    onglet_correction, onglet_prononciation, onglet_pratique = st.tabs(
        ["Structure & Correction", "Atelier de Prononciation", "Pratique Guidée"]
    )
    onglet_admin = None

# -------------------------------------------------------------------------------------
# ONGLET : STRUCTURE & CORRECTION
# -------------------------------------------------------------------------------------
with onglet_correction:
    st.markdown(
        """
        <div class="frantsay-card">
            <span class="frantsay-label">Grammaire</span>
            <h4>Analyse et correction d'une phrase</h4>
            <p style="color:#94A3B8;">Écris une phrase ou un court texte en français.
            La correction, la décomposition grammaticale et une explication
            adaptée s'affichent ci-dessous.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    texte_utilisateur = st.text_area(
        "Texte à analyser",
        placeholder="Exemple : Manger Rakoto du riz avec sa famille hier soir.",
        height=140,
        label_visibility="collapsed",
    )

    if st.button("Analyser la phrase"):
        if not texte_utilisateur.strip():
            st.error("Merci d'écrire une phrase ou un texte avant de lancer l'analyse.")
        elif not cle_api_disponible():
            afficher_carte_configuration_absente()
        else:
            try:
                with st.spinner("Analyse en cours..."):
                    prompt_utilisateur = (
                        f"Niveau scolaire de l'élève : {st.session_state.niveau}.\n\n"
                        f"Texte à corriger :\n\"\"\"\n{texte_utilisateur}\n\"\"\""
                    )
                    reponse_brute = appeler_gemini(SYSTEM_PROMPT_CORRECTION, prompt_utilisateur)
                    resultat = extraire_json(reponse_brute)

                st.markdown('<div class="frantsay-card">', unsafe_allow_html=True)
                st.markdown("<h4>Phrase corrigée</h4>", unsafe_allow_html=True)
                st.markdown(f"**{resultat.get('phrase_corrigee', '')}**")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div class="frantsay-card">', unsafe_allow_html=True)
                st.markdown("<h4>Décomposition grammaticale</h4>", unsafe_allow_html=True)
                blocs_html = ""
                classes_par_type = {
                    "Sujet": "badge-sujet",
                    "Verbe": "badge-verbe",
                    "Complément": "badge-complement",
                }
                for element in resultat.get("decomposition", []):
                    type_element = element.get("type", "Autre")
                    classe_css = classes_par_type.get(type_element, "badge-autre")
                    texte_element = element.get("texte", "")
                    blocs_html += (
                        f'<div class="badge-groupe {classe_css}">'
                        f'<span class="badge-type">{type_element}</span>'
                        f'<span class="badge-texte">{texte_element}</span>'
                        f"</div>"
                    )
                st.markdown(blocs_html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div class="frantsay-card">', unsafe_allow_html=True)
                st.markdown("<h4>Explication</h4>", unsafe_allow_html=True)
                st.write(resultat.get("explication", ""))
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div class="frantsay-card">', unsafe_allow_html=True)
                st.markdown("<h4>Conseil de prononciation</h4>", unsafe_allow_html=True)
                st.write(resultat.get("conseil_prononciation", ""))
                st.markdown("</div>", unsafe_allow_html=True)

                st.session_state.historique_corrections.insert(
                    0,
                    {
                        "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "texte": texte_utilisateur,
                        "resultat": resultat,
                    },
                )
            except json.JSONDecodeError:
                st.error(
                    "La réponse reçue n'a pas pu être analysée correctement. "
                    "Merci de réessayer."
                )
            except Exception as erreur:
                st.error(f"Une erreur est survenue : {erreur}")

    if st.session_state.historique_corrections:
        with st.expander(f"Historique ({len(st.session_state.historique_corrections)})"):
            for entree in st.session_state.historique_corrections:
                st.markdown(f"**{entree['date']}** — {entree['texte']}")
                st.markdown(f"Phrase corrigée : {entree['resultat'].get('phrase_corrigee', '')}")
                st.divider()

# -------------------------------------------------------------------------------------
# ONGLET : ATELIER DE PRONONCIATION
# -------------------------------------------------------------------------------------
with onglet_prononciation:
    st.markdown(
        """
        <div class="frantsay-card">
            <span class="frantsay-label">Phonétique</span>
            <h4>Sons difficiles pour un apprenant malgachophone</h4>
            <p style="color:#94A3B8;">Écoute la prononciation correcte des sons qui
            posent le plus de difficulté, à un rythme naturel.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for categorie in SONS_DIFFICILES:
        st.markdown('<div class="frantsay-card">', unsafe_allow_html=True)
        st.markdown(f"<h4>{categorie['titre']}</h4>", unsafe_allow_html=True)
        st.write(categorie["explication"])

        colonnes = st.columns(len(categorie["paires"]))
        for colonne, (mot_a, mot_b) in zip(colonnes, categorie["paires"]):
            with colonne:
                st.markdown(f"{mot_a} / {mot_b}")
                cle_bouton = f"ecouter_{categorie['titre']}_{mot_a}_{mot_b}"
                if st.button("Écouter", key=cle_bouton):
                    try:
                        st.audio(generer_audio(mot_a, lent=True), format="audio/mp3")
                        st.audio(generer_audio(mot_b, lent=True), format="audio/mp3")
                    except Exception as erreur:
                        st.error(f"Audio indisponible : {erreur}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="frantsay-card">
            <h4>Phrase d'entraînement personnalisée</h4>
            <p style="color:#94A3B8;">Tape une phrase, écoute-la prononcée
            correctement, puis entraîne-toi à la répéter.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    phrase_entrainement = st.text_input(
        "Phrase à écouter",
        value="Bonjour, je voudrais acheter des bananes et des oranges, s'il vous plaît.",
        label_visibility="collapsed",
    )

    colonne_normale, colonne_lente = st.columns(2)
    with colonne_normale:
        if st.button("Écouter à vitesse normale", use_container_width=True):
            if phrase_entrainement.strip():
                try:
                    st.audio(generer_audio(phrase_entrainement, lent=False), format="audio/mp3")
                except Exception as erreur:
                    st.error(f"Audio indisponible : {erreur}")
            else:
                st.warning("Merci d'écrire une phrase.")
    with colonne_lente:
        if st.button("Écouter au ralenti", use_container_width=True):
            if phrase_entrainement.strip():
                try:
                    st.audio(generer_audio(phrase_entrainement, lent=True), format="audio/mp3")
                except Exception as erreur:
                    st.error(f"Audio indisponible : {erreur}")
            else:
                st.warning("Merci d'écrire une phrase.")

# -------------------------------------------------------------------------------------
# ONGLET : PRATIQUE GUIDÉE
# -------------------------------------------------------------------------------------
with onglet_pratique:
    st.markdown(
        """
        <div class="frantsay-card">
            <span class="frantsay-label">Mise en situation</span>
            <h4>Dialogues du quotidien académique et professionnel</h4>
            <p style="color:#94A3B8;">Choisis une situation courante : un dialogue
            adapté à ton niveau est généré, avec du vocabulaire clé et un point de
            grammaire expliqué.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scenario_choisi = st.selectbox("Situation", options=SCENARIOS, label_visibility="collapsed")
    scenario_personnalise = st.text_input(
        "Ou décris ta propre situation (optionnel)",
        placeholder="Exemple : présenter un projet devant un jury",
    )

    if st.button("Générer le dialogue"):
        situation_finale = (
            scenario_personnalise.strip() if scenario_personnalise.strip() else scenario_choisi
        )
        if not cle_api_disponible():
            afficher_carte_configuration_absente()
        else:
            try:
                with st.spinner("Génération du dialogue en cours..."):
                    prompt_dialogue = (
                        f"Niveau scolaire de l'élève : {st.session_state.niveau}.\n"
                        f"Situation demandée : {situation_finale}.\n\n"
                        f"Génère le dialogue en respectant les consignes du prompt système."
                    )
                    dialogue_genere = appeler_gemini(SYSTEM_PROMPT_DIALOGUE, prompt_dialogue)

                st.markdown('<div class="frantsay-card">', unsafe_allow_html=True)
                st.markdown(dialogue_genere)
                st.markdown("</div>", unsafe_allow_html=True)

                try:
                    audio_dialogue = generer_audio(
                        dialogue_genere.replace("*", "").replace("#", "")
                    )
                    st.audio(audio_dialogue, format="audio/mp3")
                except Exception:
                    pass

                st.session_state.historique_dialogues.insert(
                    0,
                    {
                        "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "situation": situation_finale,
                        "dialogue": dialogue_genere,
                    },
                )
            except Exception as erreur:
                st.error(f"Une erreur est survenue : {erreur}")

    if st.session_state.historique_dialogues:
        with st.expander(f"Historique ({len(st.session_state.historique_dialogues)})"):
            for entree in st.session_state.historique_dialogues:
                st.markdown(f"**{entree['date']}** — {entree['situation']}")
                st.markdown(entree["dialogue"])
                st.divider()

# -------------------------------------------------------------------------------------
# ONGLET : CONFIGURATION ADMIN
# -------------------------------------------------------------------------------------
if onglet_admin is not None:
    with onglet_admin:
        st.markdown(
            """
            <div class="frantsay-card">
                <span class="frantsay-label">Administration</span>
                <h4>Configuration globale de la plateforme</h4>
                <p style="color:#94A3B8;">La clé API Gemini enregistrée ici est
                utilisée pour tous les utilisateurs de la plateforme. Les élèves
                n'ont pas besoin de la saisir ni de la voir.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cle_actuelle = st.session_state.config_globale.get("gemini_api_key", "")
        statut = "Une clé est actuellement configurée." if cle_actuelle else "Aucune clé n'est configurée."
        st.markdown(f"**Statut** : {statut}")

        nouvelle_cle = st.text_input(
            "Clé API Google Gemini",
            type="password",
            placeholder="AIza...",
        )

        if st.button("Enregistrer la clé"):
            if not nouvelle_cle.strip():
                st.error("Merci de saisir une clé API valide.")
            else:
                sauvegarder_config(nouvelle_cle.strip())
                st.session_state.config_globale = charger_config()
                st.success("La clé API a été enregistrée pour l'ensemble de la plateforme.")

        if cle_actuelle:
            if st.button("Retirer la clé actuelle"):
                sauvegarder_config("")
                st.session_state.config_globale = charger_config()
                st.success("La clé API a été retirée.")

# =====================================================================================
# 13. PIED DE PAGE
# =====================================================================================

st.markdown(
    """
    <div class="frantsay-footer">
    FRANTSAY — Plateforme d'apprentissage du français pour Madagascar.
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================================
# 14. INSTALLATION ET LANCEMENT
# =====================================================================================
#
# 1) Mettre à jour requirements.txt avec :
#       streamlit
#       google-genai
#       gTTS
#
#    (le code bascule automatiquement sur l'ancien SDK google-generativeai s'il est
#    installé à la place de google-genai, mais google-genai est désormais le SDK
#    recommandé par Google et doit être utilisé en priorité)
#
# 2) Installer les dépendances :
#       pip install streamlit google-genai gTTS
#
# 3) Lancer l'application :
#       streamlit run frantsay_app.py
#
# 4) Se connecter avec l'adresse admin@frantsay.mg (ou l'adresse définie dans
#    ADMIN_EMAIL) pour accéder à l'onglet "Configuration Admin" et enregistrer la
#    clé API Gemini. Tout autre e-mail valide donne accès direct aux modules
#    d'apprentissage, sans jamais voir la clé API.
#
# Remarque : la clé API globale est stockée dans le fichier local
# "frantsay_config.json", situé à côté de ce script. Sur un hébergement comme
# Streamlit Community Cloud, ce fichier persiste tant que l'application n'est pas
# redéployée depuis GitHub (un redéploiement réinitialise le système de fichiers).
#
# =====================================================================================
