# -*- coding: utf-8 -*-
"""
=====================================================================================
 FRANTSAY
 Plateforme d'apprentissage du français pour les élèves et étudiants à Madagascar.

 Direction artistique : Dashboard IA, Glassmorphism sombre.
 Stack : Streamlit + Google Gemini (SDK google-genai) + gTTS
=====================================================================================
"""

import streamlit as st
import json
import re
import io
import datetime

# =====================================================================================
# 1. CONSTANTES
# =====================================================================================

NOM_MODELE_GEMINI = "gemini-2.0-flash"
NIVEAUX = ["Collège", "Lycée", "Université"]

# =====================================================================================
# 2. CONFIGURATION DE LA PAGE
# =====================================================================================

st.set_page_config(
    page_title="FRANTSAY",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================================
# 3. CSS — GLASSMORPHISM SOMBRE (INSPIRATION DASHBOARD IA)
# =====================================================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% -10%, rgba(156, 167, 222, 0.14) 0%, transparent 40%),
        radial-gradient(circle at 90% 10%, rgba(236, 99, 13, 0.10) 0%, transparent 42%),
        radial-gradient(circle at 50% 100%, rgba(156, 167, 222, 0.08) 0%, transparent 50%),
        #05060B;
    color: #E7E9F2;
}

h1, h2, h3, h4, h5, p, span, label, div {
    color: #E7E9F2;
}

/* ---------- Header dashboard ---------- */
.frantsay-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
    background: rgba(13, 17, 29, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.6rem;
}
.frantsay-header .titre-bloc .marque {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0;
    color: #F4F5FA;
}
.frantsay-header .titre-bloc p {
    color: #9096A8;
    font-size: 0.92rem;
    margin-top: 0.3rem;
    max-width: 480px;
}
.badge-ai-active {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(52, 211, 153, 0.10);
    border: 1px solid rgba(52, 211, 153, 0.35);
    color: #6EE7B7;
    padding: 0.4rem 0.95rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.badge-ai-active .point {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #34D399;
    box-shadow: 0 0 8px 2px rgba(52, 211, 153, 0.7);
}
.badge-ai-inactif {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(156, 167, 222, 0.10);
    border: 1px solid rgba(156, 167, 222, 0.35);
    color: #C3C9F0;
    padding: 0.4rem 0.95rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.badge-ai-inactif .point {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #9CA7DE;
    box-shadow: 0 0 8px 2px rgba(156, 167, 222, 0.7);
}

/* ---------- Cartes glassmorphism ---------- */
.frantsay-card {
    background: rgba(13, 17, 29, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.2rem;
    transition: border-color 0.2s ease-in-out;
}
.frantsay-card:hover {
    border-color: rgba(156, 167, 222, 0.28);
}
.frantsay-card h4 {
    margin-top: 0;
    font-weight: 700;
    color: #F4F5FA;
}
.frantsay-eyebrow {
    display: inline-block;
    color: #9CA7DE;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

/* ---------- Note douce (jamais de blocage rouge) ---------- */
.frantsay-note {
    background: rgba(156, 167, 222, 0.08);
    border: 1px solid rgba(156, 167, 222, 0.3);
    border-radius: 16px;
    padding: 1rem 1.3rem;
    color: #C3C9F0;
    font-size: 0.9rem;
    margin-bottom: 1.1rem;
}

/* ---------- Capsules Sujet / Verbe / Complément ---------- */
.capsule {
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    border-radius: 14px;
    padding: 0.55rem 1rem;
    margin: 0.3rem 0.45rem 0.3rem 0;
    min-width: 120px;
    border: 1px solid transparent;
    backdrop-filter: blur(6px);
}
.capsule .capsule-type {
    font-size: 0.64rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.8;
}
.capsule .capsule-texte {
    font-size: 1rem;
    font-weight: 600;
    margin-top: 0.15rem;
}
.capsule-sujet {
    background: rgba(156, 167, 222, 0.12);
    border-color: rgba(156, 167, 222, 0.35);
    color: #C3C9F0;
}
.capsule-verbe {
    background: rgba(110, 231, 183, 0.10);
    border-color: rgba(110, 231, 183, 0.32);
    color: #6EE7B7;
}
.capsule-complement {
    background: rgba(236, 99, 13, 0.12);
    border-color: rgba(236, 99, 13, 0.35);
    color: #F3A56C;
}
.capsule-autre {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.14);
    color: #C7CAD6;
}

/* ---------- Champs de saisie ---------- */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    background-color: rgba(255, 255, 255, 0.04) !important;
    color: #E7E9F2 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #9CA7DE !important;
    box-shadow: 0 0 0 1px #9CA7DE !important;
}

/* ---------- Boutons néon ---------- */
div.stButton > button {
    background: linear-gradient(90deg, #EC630D, #F3894A);
    color: #05060B;
    font-weight: 700;
    border-radius: 12px;
    border: none;
    padding: 0.68rem 1.7rem;
    transition: all 0.22s ease-in-out;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 26px rgba(236, 99, 13, 0.55), 0 8px 22px rgba(0, 0, 0, 0.35);
    background: linear-gradient(90deg, #F3894A, #EC630D);
}

/* ---------- Onglets ---------- */
button[data-baseweb="tab"] {
    font-weight: 600;
    font-size: 0.95rem;
    color: #9096A8 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #C3C9F0 !important;
}
div[data-baseweb="tab-highlight"] {
    background-color: #9CA7DE !important;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #07080F;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}
section[data-testid="stSidebar"] * {
    color: #C7CAD6;
}

.frantsay-footer {
    text-align: center;
    color: #4B5063;
    font-size: 0.8rem;
    padding: 1.8rem 0 0.6rem 0;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# =====================================================================================
# 4. GESTION TRANSPARENTE DE LA CLÉ API
# =====================================================================================


def obtenir_cle_api() -> str:
    """
    Récupère la clé API Gemini : en priorité dans les secrets Streamlit, sinon dans
    la clé saisie manuellement par l'utilisateur en session (jamais de blocage).
    """
    try:
        cle_secrete = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        cle_secrete = ""

    if cle_secrete:
        return cle_secrete

    return st.session_state.get("cle_api_manuelle", "").strip()


def cle_api_disponible() -> bool:
    return bool(obtenir_cle_api())


def cle_api_depuis_secrets() -> bool:
    try:
        return bool(st.secrets.get("GEMINI_API_KEY", ""))
    except Exception:
        return False


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
Tu es un professeur de français qui conçoit des missions pédagogiques interactives
pour des apprenants malgaches, autour de situations de la vie quotidienne.

Ta mission : générer un court dialogue réaliste en français (6 à 10 répliques),
mettant en scène une situation quotidienne à Madagascar (marché, école, université,
entretien, administration, transport, famille, vie de bureau...).

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

MISSIONS = [
    "Négocier des prix au marché",
    "Se présenter le premier jour d'université",
    "Passer un entretien d'embauche",
    "Demander son chemin dans une nouvelle ville",
    "Prendre un taxi-brousse pour un long trajet",
    "Faire une démarche dans une administration",
    "Participer à une réunion de travail",
    "Discuter en famille autour du repas",
]

# =====================================================================================
# 7. FONCTIONS D'ACCÈS À GEMINI ET À LA SYNTHÈSE VOCALE
# =====================================================================================


def appeler_gemini(system_prompt: str, user_prompt: str) -> str:
    """Appelle Google Gemini avec le SDK récent google-genai."""
    cle_api = obtenir_cle_api()
    if not cle_api:
        raise ValueError("Clé API manquante.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=cle_api)
    reponse = client.models.generate_content(
        model=NOM_MODELE_GEMINI,
        contents=user_prompt,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
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


def afficher_note_cle_manquante() -> None:
    """Rappel discret, jamais bloquant ni rouge, invitant à ajouter la clé API."""
    st.markdown(
        """
        <div class="frantsay-note">
        Ajoute ta clé API Gemini dans la barre latérale pour activer cette
        fonctionnalité — cela prend quelques secondes.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================================
# 8. INITIALISATION DE L'ÉTAT DE SESSION
# =====================================================================================

if "niveau" not in st.session_state:
    st.session_state.niveau = "Lycée"

if "cle_api_manuelle" not in st.session_state:
    st.session_state.cle_api_manuelle = ""

if "historique_corrections" not in st.session_state:
    st.session_state.historique_corrections = []

if "historique_dialogues" not in st.session_state:
    st.session_state.historique_dialogues = []

# =====================================================================================
# 9. BARRE LATÉRALE
# =====================================================================================

with st.sidebar:
    st.markdown("### Espace d'apprentissage")

    niveau_choisi = st.selectbox(
        "Niveau d'études",
        options=NIVEAUX,
        index=NIVEAUX.index(st.session_state.niveau),
    )
    st.session_state.niveau = niveau_choisi

    st.divider()

    st.markdown("### Connexion IA")
    if cle_api_depuis_secrets():
        st.markdown(
            """
            <div class="frantsay-note" style="margin-bottom:0;">
            La clé API Gemini est déjà configurée pour cette plateforme.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        cle_saisie = st.text_input(
            "Clé API Gemini",
            value=st.session_state.cle_api_manuelle,
            type="password",
            placeholder="AIza...",
            help="Obtiens une clé gratuite sur aistudio.google.com",
        )
        st.session_state.cle_api_manuelle = cle_saisie

        if cle_saisie.strip():
            st.markdown(
                '<span class="badge-ai-active"><span class="point"></span>'
                "Clé enregistrée pour cette session</span>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("Aucune clé saisie pour le moment.")

# =====================================================================================
# 10. HEADER DASHBOARD
# =====================================================================================

badge_html = (
    '<span class="badge-ai-active"><span class="point"></span>AI Active</span>'
    if cle_api_disponible()
    else '<span class="badge-ai-inactif"><span class="point"></span>En attente de connexion</span>'
)

st.markdown(
    f"""
    <div class="frantsay-header">
        <div class="titre-bloc">
            <p class="marque">FRANTSAY</p>
            <p>Plateforme d'apprentissage du français pour les élèves et étudiants
            à Madagascar — {st.session_state.niveau}.</p>
        </div>
        {badge_html}
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================================
# 11. ONGLETS PRINCIPAUX
# =====================================================================================

onglet_correction, onglet_prononciation, onglet_pratique = st.tabs(
    ["Structure & Correction", "Atelier de Prononciation", "Missions du Quotidien"]
)

# -------------------------------------------------------------------------------------
# ONGLET : STRUCTURE & CORRECTION
# -------------------------------------------------------------------------------------
with onglet_correction:
    st.markdown(
        """
        <div class="frantsay-card">
            <span class="frantsay-eyebrow">Grammaire</span>
            <h4>Analyse et correction d'une phrase</h4>
            <p style="color:#9096A8;">Écris une phrase ou un court texte en français.
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

    if not cle_api_disponible():
        afficher_note_cle_manquante()

    if st.button("Analyser la phrase"):
        if not texte_utilisateur.strip():
            st.markdown(
                '<div class="frantsay-note">Écris une phrase avant de lancer '
                "l'analyse.</div>",
                unsafe_allow_html=True,
            )
        elif not cle_api_disponible():
            afficher_note_cle_manquante()
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
                    "Sujet": "capsule-sujet",
                    "Verbe": "capsule-verbe",
                    "Complément": "capsule-complement",
                }
                for element in resultat.get("decomposition", []):
                    type_element = element.get("type", "Autre")
                    classe_css = classes_par_type.get(type_element, "capsule-autre")
                    texte_element = element.get("texte", "")
                    blocs_html += (
                        f'<div class="capsule {classe_css}">'
                        f'<span class="capsule-type">{type_element}</span>'
                        f'<span class="capsule-texte">{texte_element}</span>'
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
                st.markdown(
                    '<div class="frantsay-note">La réponse reçue n\'a pas pu être '
                    "analysée correctement. Merci de réessayer.</div>",
                    unsafe_allow_html=True,
                )
            except Exception as erreur:
                st.markdown(
                    f'<div class="frantsay-note">Une erreur est survenue : '
                    f"{erreur}</div>",
                    unsafe_allow_html=True,
                )

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
            <span class="frantsay-eyebrow">Phonétique</span>
            <h4>Sons difficiles pour un apprenant malgachophone</h4>
            <p style="color:#9096A8;">Écoute la prononciation correcte des sons qui
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
                        st.markdown(
                            f'<div class="frantsay-note">Audio indisponible : '
                            f"{erreur}</div>",
                            unsafe_allow_html=True,
                        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="frantsay-card">
            <h4>Phrase d'entraînement personnalisée</h4>
            <p style="color:#9096A8;">Tape une phrase, écoute-la prononcée
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
                    st.markdown(
                        f'<div class="frantsay-note">Audio indisponible : '
                        f"{erreur}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div class="frantsay-note">Écris une phrase avant d\'écouter.'
                    "</div>",
                    unsafe_allow_html=True,
                )
    with colonne_lente:
        if st.button("Écouter au ralenti", use_container_width=True):
            if phrase_entrainement.strip():
                try:
                    st.audio(generer_audio(phrase_entrainement, lent=True), format="audio/mp3")
                except Exception as erreur:
                    st.markdown(
                        f'<div class="frantsay-note">Audio indisponible : '
                        f"{erreur}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div class="frantsay-note">Écris une phrase avant d\'écouter.'
                    "</div>",
                    unsafe_allow_html=True,
                )

# -------------------------------------------------------------------------------------
# ONGLET : MISSIONS DU QUOTIDIEN
# -------------------------------------------------------------------------------------
with onglet_pratique:
    st.markdown(
        """
        <div class="frantsay-card">
            <span class="frantsay-eyebrow">Mise en situation</span>
            <h4>Missions du quotidien</h4>
            <p style="color:#9096A8;">Choisis une mission : un dialogue adapté à
            ton niveau est généré, avec du vocabulaire clé et un point de grammaire
            expliqué.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mission_choisie = st.selectbox("Mission", options=MISSIONS, label_visibility="collapsed")
    mission_personnalisee = st.text_input(
        "Ou décris ta propre mission (optionnel)",
        placeholder="Exemple : présenter un projet devant un jury",
    )

    if not cle_api_disponible():
        afficher_note_cle_manquante()

    if st.button("Lancer la mission"):
        situation_finale = (
            mission_personnalisee.strip() if mission_personnalisee.strip() else mission_choisie
        )
        if not cle_api_disponible():
            afficher_note_cle_manquante()
        else:
            try:
                with st.spinner("Génération de la mission en cours..."):
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
                st.markdown(
                    f'<div class="frantsay-note">Une erreur est survenue : '
                    f"{erreur}</div>",
                    unsafe_allow_html=True,
                )

    if st.session_state.historique_dialogues:
        with st.expander(f"Historique ({len(st.session_state.historique_dialogues)})"):
            for entree in st.session_state.historique_dialogues:
                st.markdown(f"**{entree['date']}** — {entree['situation']}")
                st.markdown(entree["dialogue"])
                st.divider()

# =====================================================================================
# 12. PIED DE PAGE
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
# 13. INSTALLATION ET LANCEMENT
# =====================================================================================
#
# 1) Contenu exact du fichier requirements.txt :
#
#       streamlit
#       google-genai
#       gTTS
#
# 2) Installer les dépendances :
#       pip install streamlit google-genai gTTS
#
# 3) (Optionnel mais recommandé) Configurer la clé API dans les secrets Streamlit
#    pour qu'elle soit déjà active pour tous les visiteurs, sans qu'ils aient à la
#    saisir : créer un fichier .streamlit/secrets.toml contenant :
#
#       GEMINI_API_KEY = "colle-ta-cle-ici"
#
#    Sur Streamlit Community Cloud, cela se fait depuis Manage app > Settings >
#    Secrets. Si aucun secret n'est défini, un champ de saisie discret apparaît
#    automatiquement dans la barre latérale pour chaque visiteur.
#
# 4) Lancer l'application :
#       streamlit run frantsay_app.py
#
# =====================================================================================
