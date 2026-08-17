# -*- coding: utf-8 -*-
"""
=====================================================================================
 FrançaisPro Madagascar 🇲🇬
 Application web pédagogique interactive pour aider les élèves et étudiants
 malgaches à surmonter leurs difficultés en français
 (grammaire, conjugaison, structure de phrase, élocution).

 Auteur   : Développeur Full-Stack Senior / Expert pédagogie FLE
 Stack    : Streamlit + OpenAI / Google Gemini + gTTS
=====================================================================================
"""

import streamlit as st
import io
import json
import random
import datetime

# =====================================================================================
# 1. CONFIGURATION GÉNÉRALE DE LA PAGE
# =====================================================================================

st.set_page_config(
    page_title="FrançaisPro Madagascar 🇲🇬",
    page_icon="🇲🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================================
# 2. CSS PERSONNALISÉ (DESIGN CHALEUREUX ET PÉDAGOGIQUE)
# =====================================================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"]  {
    font-family: 'Poppins', sans-serif;
}

/* Fond général */
.stApp {
    background: linear-gradient(180deg, #f4fbf6 0%, #eef7fb 100%);
}

/* Bandeau d'en-tête */
.mg-header {
    background: linear-gradient(120deg, #007A3D 0%, #1B8A9C 55%, #0A5C8A 100%);
    padding: 2.1rem 2.4rem;
    border-radius: 22px;
    box-shadow: 0 12px 30px rgba(0, 90, 70, 0.25);
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}
.mg-header::after {
    content: "";
    position: absolute;
    right: -60px;
    top: -60px;
    width: 220px;
    height: 220px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}
.mg-header h1 {
    color: white;
    font-weight: 800;
    font-size: 2.1rem;
    margin: 0 0 0.35rem 0;
    letter-spacing: -0.5px;
}
.mg-header p {
    color: #eafff2;
    font-size: 1.02rem;
    margin: 0;
    max-width: 780px;
    line-height: 1.5;
}
.mg-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.7rem;
    margin-right: 0.4rem;
    border: 1px solid rgba(255,255,255,0.35);
}

/* Cartes de contenu */
.mg-card {
    background: white;
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 6px 18px rgba(20, 60, 50, 0.07);
    border: 1px solid #e6f1ea;
    margin-bottom: 1.1rem;
}

.mg-card h4 {
    margin-top: 0;
    color: #045c45;
}

.mg-pill {
    display: inline-block;
    background: #e6f7ee;
    color: #037a4c;
    border: 1px solid #b9e8d0;
    padding: 0.15rem 0.65rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.mg-sound-card {
    background: #fbfdff;
    border: 1px solid #dbe9f3;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.9rem;
}

.mg-sound-title {
    font-weight: 700;
    color: #0A5C8A;
    font-size: 1.05rem;
    margin-bottom: 0.25rem;
}

.mg-footer {
    text-align: center;
    color: #6b7c76;
    font-size: 0.82rem;
    padding: 1.4rem 0 0.4rem 0;
}

/* Boutons */
div.stButton > button {
    background: linear-gradient(120deg, #007A3D, #0A5C8A);
    color: white;
    font-weight: 600;
    border-radius: 12px;
    border: none;
    padding: 0.55rem 1.3rem;
    transition: all 0.2s ease-in-out;
}
div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(10, 92, 138, 0.28);
}

/* Tabs */
button[data-baseweb="tab"] {
    font-weight: 600;
    font-size: 1rem;
}

section[data-testid="stSidebar"] {
    background: #f0f7f4;
    border-right: 1px solid #dfeee6;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =====================================================================================
# 3. PROMPT SYSTÈME EMBARQUÉ (LE CERVEAU IA)
# =====================================================================================

SYSTEM_PROMPT_CORRECTEUR = """
Tu es "Ramose Français", un professeur de français bienveillant, patient et expert en
didactique du Français Langue Étrangère (FLE), spécialisé dans l'accompagnement des
apprenants malgaches (Madagascar).

CONTEXTE IMPORTANT SUR LES APPRENANTS :
Les élèves malgaches rencontrent des difficultés récurrentes dues à des interférences
avec leur langue maternelle, le malagasy :
1. Structure de phrase : en malagasy, l'ordre habituel est Verbe-Objet-Sujet (VOS),
   ce qui provoque des inversions du type "Mange Rakoto du riz" au lieu de
   "Rakoto mange du riz".
2. Absence de genre grammatical : le malagasy ne marque pas le masculin/féminin, d'où
   des confusions fréquentes sur "le/la", "un/une", "mon/ma", "il/elle", les accords
   d'adjectifs, etc.
3. Système verbal différent : le malagasy exprime le temps différemment (préfixes
   comme "no-", "ho-", "mi-"), ce qui complique l'apprentissage des temps français
   (présent, passé composé, imparfait, futur, subjonctif...).
4. Prononciation : difficultés sur les sons u/ou, b/v, p/f, et les voyelles nasales
   (an, en, on, in), car ces sons/oppositions n'existent pas de la même façon en
   malagasy.

TA MISSION :
Quand un apprenant te soumet une phrase ou un texte en français à corriger, tu dois
TOUJOURS répondre en respectant EXACTEMENT la structure suivante, en Markdown, avec
ces titres et emojis, sans jamais les omettre :

🟢 **Correction directe**
- Donne la version corrigée de la phrase, propre et naturelle.
- Si la phrase était déjà correcte, félicite l'élève et propose une variante plus
  riche ou plus naturelle.

🧩 **Décomposition structurelle (Sujet / Verbe / Complément)**
- Découpe la phrase corrigée en indiquant clairement : [Sujet] / [Verbe] / [Complément]
  (et éventuellement les compléments circonstanciels).
- Utilise un format clair, par exemple :
  Sujet : ... | Verbe : ... | Complément : ...

💡 **Explication simple**
- Explique la règle de grammaire concernée avec des mots simples, comme si tu
  parlais à un adolescent.
- Si l'erreur vient probablement d'une traduction littérale du malagasy (inversion
  verbe/sujet, absence de genre, temps verbal), explique EXPLICITEMENT ce lien
  ("En malagasy, on dirait plutôt... c'est pour cela qu'on a tendance à...").
- Reste toujours bienveillant, jamais moqueur, et encourageant.

🔊 **Conseil de prononciation**
- Repère dans la phrase corrigée les mots contenant des sons difficiles pour un
  malgachophone (u/ou, b/v, p/f, voyelles nasales an/en/on/in).
- Donne un petit conseil articulatoire simple pour bien prononcer ces mots
  (position de la bouche, des lèvres, etc.) et propose éventuellement un mot
  proche en malagasy ou un moyen mnémotechnique si pertinent.

RÈGLES DE STYLE :
- Adapte le niveau de vocabulaire et la complexité de tes explications au niveau
  scolaire indiqué (Collège, Lycée, ou Université).
- Ne sois jamais condescendant. Utilise un ton chaleureux, encourageant, proche
  d'un grand frère ou d'une grande sœur qui explique patiemment.
- Reste concis mais complet : chaque section doit apporter une vraie valeur
  pédagogique.
- Réponds toujours en français.
"""

SYSTEM_PROMPT_DIALOGUE = """
Tu es "Ramose Français", un professeur de français créatif et bienveillant qui conçoit
des dialogues pédagogiques pour des apprenants malgaches.

Ta mission : générer un court dialogue réaliste en français (6 à 10 répliques),
mettant en scène une situation de la vie quotidienne à Madagascar (marché, école,
entretien d'embauche, transport en taxi-brousse, famille, administration...).

CONSIGNES :
- Utilise des prénoms malgaches courants (Rakoto, Rabe, Voahangy, Hery, Fara,
  Tiana, Nirina, Mialy, etc.) et éventuellement des lieux locaux (Analakely,
  marché de Anosibe, gare routière...).
- Adapte le niveau de langue au niveau scolaire indiqué (Collège = phrases simples
  et vocabulaire courant ; Lycée = phrases plus riches ; Université = registre plus
  soutenu et nuancé, éventuellement avec du vocabulaire professionnel).
- Après le dialogue, ajoute une section "📘 Vocabulaire à retenir" avec 4 à 6
  mots ou expressions clés expliqués simplement.
- Ajoute une section "🎯 Point de grammaire mis en avant" qui explique une règle
  illustrée dans le dialogue (accord, temps verbal, structure de phrase...), en
  faisant si pertinent le lien avec les erreurs typiques dues au malagasy.
- Structure ta réponse en Markdown avec des titres clairs.
- Réponds toujours en français.
"""

# =====================================================================================
# 4. DONNÉES PÉDAGOGIQUES STATIQUES (STUDIO D'ÉLOCUTION)
# =====================================================================================

SONS_DIFFICILES = [
    {
        "titre": "🔤 Le son [u] vs [ou]",
        "explication": (
            "En malagasy, l'opposition entre le [u] français (comme dans « lune »)"
            " et le [ou] français (comme dans « joue ») n'existe pas de la même"
            " manière. On confond souvent ces deux sons car ils semblent proches"
            " à l'oreille. Pour le [u], arrondissez fortement les lèvres et poussez"
            " la langue vers l'avant. Pour le [ou], arrondissez aussi les lèvres"
            " mais reculez la langue vers l'arrière de la bouche."
        ),
        "paires_minimales": [
            ("tu", "tout"),
            ("rue", "roue"),
            ("dessus", "dessous"),
            ("pull", "poule"),
        ],
    },
    {
        "titre": "🔤 Le son [b] vs [v]",
        "explication": (
            "Le [b] est une consonne occlusive (les lèvres se ferment complètement"
            " puis s'ouvrent d'un coup), alors que le [v] est une consonne fricative"
            " (les lèvres/dents restent proches et l'air passe en continu, cela"
            " vibre). Beaucoup d'apprenants malgaches prononcent le [v] comme un"
            " [b], car en malagasy ces deux sons peuvent se confondre selon les"
            " dialectes. Astuce : pour le [v], posez vos dents du haut sur votre"
            " lèvre inférieure et laissez l'air vibrer en continu, sans fermer la"
            " bouche."
        ),
        "paires_minimales": [
            ("bas", "vas"),
            ("bœuf", "veuf"),
            ("bin", "vin"),
            ("bous", "vous"),
        ],
    },
    {
        "titre": "🔤 Le son [p] vs [f]",
        "explication": (
            "Le [p] est occlusif (les lèvres se ferment puis explosent) alors que"
            " le [f] est fricatif continu (l'air passe entre les dents du haut et"
            " la lèvre du bas). Entraînez-vous à sentir la différence : pour le"
            " [p], mettez la main devant la bouche, vous devez sentir un petit"
            " souffle bref et sec ; pour le [f], le souffle est continu et long."
        ),
        "paires_minimales": [
            ("pou", "fou"),
            ("pin", "fin"),
            ("panne", "fane"),
            ("port", "fort"),
        ],
    },
    {
        "titre": "🔤 Les voyelles nasales (an / en / on / in)",
        "explication": (
            "Le français possède des voyelles nasales qui n'existent pas telles"
            " quelles en malagasy : l'air passe à la fois par la bouche et par le"
            " nez. Beaucoup d'apprenants ont tendance à prononcer un « n » ou un"
            " « ng » très marqué après la voyelle au lieu de nasaliser la voyelle"
            " elle-même. Entraînez-vous en pinçant légèrement le nez : si le son"
            " change beaucoup, c'est que vous nasalisez bien."
        ),
        "paires_minimales": [
            ("bon", "banc"),
            ("vin", "vent"),
            ("son", "sang"),
            ("pain", "pont"),
        ],
    },
]

SCENARIOS_DIALOGUE = [
    "Au marché (acheter des fruits et légumes, négocier le prix)",
    "À l'école (discuter avec un professeur ou un camarade)",
    "Un entretien d'embauche pour un premier emploi",
    "Dans un taxi-brousse pendant un voyage",
    "En famille, autour du repas du soir",
    "À la banque ou dans une administration",
]

NIVEAUX = ["Collège", "Lycée", "Université"]

# =====================================================================================
# 5. INITIALISATION DE L'ÉTAT DE SESSION
# =====================================================================================

if "historique_corrections" not in st.session_state:
    st.session_state.historique_corrections = []

if "historique_dialogues" not in st.session_state:
    st.session_state.historique_dialogues = []

if "provider" not in st.session_state:
    st.session_state.provider = "OpenAI"

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "niveau" not in st.session_state:
    st.session_state.niveau = "Lycée"

# =====================================================================================
# 6. FONCTIONS UTILITAIRES : APPELS AUX MODÈLES IA
# =====================================================================================


def appeler_openai(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Appelle l'API OpenAI (Chat Completions) et retourne le texte de la réponse."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    reponse = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=1200,
    )
    return reponse.choices[0].message.content


def appeler_gemini(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Appelle l'API Google Gemini et retourne le texte de la réponse."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    modele = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
    )
    reponse = modele.generate_content(user_prompt)
    return reponse.text


def appeler_llm(system_prompt: str, user_prompt: str) -> str:
    """Point d'entrée unique : redirige vers OpenAI ou Gemini selon la configuration."""
    provider = st.session_state.provider
    api_key = st.session_state.api_key

    if not api_key:
        raise ValueError(
            "Aucune clé API n'a été renseignée. Merci de l'ajouter dans la barre "
            "latérale avant de continuer."
        )

    if provider == "OpenAI":
        return appeler_openai(system_prompt, user_prompt, api_key)
    elif provider == "Google Gemini":
        return appeler_gemini(system_prompt, user_prompt, api_key)
    else:
        raise ValueError(f"Fournisseur IA inconnu : {provider}")


def transcrire_audio_openai(audio_bytes: bytes, api_key: str) -> str:
    """Transcrit un enregistrement audio en texte via Whisper (OpenAI)."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    fichier_audio = io.BytesIO(audio_bytes)
    fichier_audio.name = "enregistrement.wav"
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=fichier_audio,
        language="fr",
    )
    return transcription.text


def transcrire_audio_gemini(audio_bytes: bytes, api_key: str) -> str:
    """Transcrit un enregistrement audio en texte via Google Gemini."""
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    modele = genai.GenerativeModel(model_name="gemini-1.5-flash")
    reponse = modele.generate_content(
        [
            "Transcris fidèlement cet enregistrement audio en français. "
            "Retourne uniquement le texte transcrit, sans commentaire additionnel.",
            {"mime_type": "audio/wav", "data": audio_bytes},
        ]
    )
    return reponse.text


def transcrire_audio(audio_bytes: bytes) -> str:
    """Point d'entrée unique pour la transcription audio."""
    provider = st.session_state.provider
    api_key = st.session_state.api_key

    if not api_key:
        raise ValueError(
            "Aucune clé API n'a été renseignée. Merci de l'ajouter dans la barre "
            "latérale avant de continuer."
        )

    if provider == "OpenAI":
        return transcrire_audio_openai(audio_bytes, api_key)
    elif provider == "Google Gemini":
        return transcrire_audio_gemini(audio_bytes, api_key)
    else:
        raise ValueError(f"Fournisseur IA inconnu : {provider}")


def generer_audio(texte: str, lent: bool = False) -> io.BytesIO:
    """Génère un fichier audio MP3 (voix française) à partir d'un texte via gTTS."""
    from gtts import gTTS

    tts = gTTS(text=texte, lang="fr", slow=lent)
    tampon = io.BytesIO()
    tts.write_to_fp(tampon)
    tampon.seek(0)
    return tampon


# =====================================================================================
# 7. BARRE LATÉRALE (SIDEBAR) : CONFIGURATION
# =====================================================================================

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown(
        "Connecte ton assistant IA pour activer les corrections, les dialogues "
        "et la transcription audio."
    )

    provider_choisi = st.radio(
        "🤖 Modèle d'intelligence artificielle",
        options=["OpenAI", "Google Gemini"],
        index=0 if st.session_state.provider == "OpenAI" else 1,
        help="Choisis le fournisseur d'IA que tu souhaites utiliser.",
    )
    st.session_state.provider = provider_choisi

    if provider_choisi == "OpenAI":
        cle_saisie = st.text_input(
            "🔑 Clé API OpenAI",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-...",
            help="Ta clé est utilisée uniquement pendant cette session et n'est "
            "jamais enregistrée sur un serveur.",
        )
    else:
        cle_saisie = st.text_input(
            "🔑 Clé API Google Gemini",
            value=st.session_state.api_key,
            type="password",
            placeholder="AIza...",
            help="Ta clé est utilisée uniquement pendant cette session et n'est "
            "jamais enregistrée sur un serveur.",
        )
    st.session_state.api_key = cle_saisie

    st.divider()

    niveau_choisi = st.selectbox(
        "🎓 Niveau d'études",
        options=NIVEAUX,
        index=NIVEAUX.index(st.session_state.niveau),
        help="Les explications et les dialogues générés seront adaptés à ce niveau.",
    )
    st.session_state.niveau = niveau_choisi

    st.divider()

    st.markdown(
        """
        <div class="mg-card" style="padding:1rem;">
        <h4 style="margin-bottom:0.4rem;">💚 À propos</h4>
        <p style="font-size:0.85rem; color:#4a5a54; line-height:1.5;">
        <b>FrançaisPro Madagascar</b> est un outil pédagogique conçu pour
        accompagner les élèves et étudiants malgaches dans l'apprentissage du
        français, en tenant compte des spécificités linguistiques du malagasy.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🗑️ Réinitialiser l'historique", use_container_width=True):
        st.session_state.historique_corrections = []
        st.session_state.historique_dialogues = []
        st.success("Historique réinitialisé !")

# =====================================================================================
# 8. EN-TÊTE PRINCIPAL
# =====================================================================================

st.markdown(
    f"""
    <div class="mg-header">
        <h1>🇲🇬 FrançaisPro Madagascar</h1>
        <p>
        Ton compagnon intelligent pour progresser en français : corrige tes phrases,
        comprends <b>pourquoi</b> c'est une faute, entraîne ta prononciation et
        exerce-toi avec des dialogues du quotidien malgache.
        </p>
        <span class="mg-badge">🎓 Niveau actuel : {st.session_state.niveau}</span>
        <span class="mg-badge">🤖 IA : {st.session_state.provider}</span>
        <span class="mg-badge">📅 {datetime.date.today().strftime('%d/%m/%Y')}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.api_key:
    st.warning(
        "⚠️ Merci de renseigner ta clé API dans la barre latérale (⚙️ Configuration) "
        "pour activer toutes les fonctionnalités intelligentes de l'application."
    )

# =====================================================================================
# 9. ONGLETS PRINCIPAUX
# =====================================================================================

onglet_correcteur, onglet_elocution, onglet_situation = st.tabs(
    ["📝 Correcteur & Structure", "🎙️ Studio d'Élocution", "🎭 Mise en Situation"]
)

# -------------------------------------------------------------------------------------
# ONGLET 1 : CORRECTEUR & STRUCTURE
# -------------------------------------------------------------------------------------
with onglet_correcteur:
    st.markdown(
        """
        <div class="mg-card">
        <span class="mg-pill">Grammaire · Structure · Conjugaison</span>
        <h4>✍️ Écris ta phrase ou ton petit texte en français</h4>
        <p style="color:#516059;">
        Notre professeur virtuel va corriger ton texte, décomposer la phrase en
        Sujet / Verbe / Complément, t'expliquer la règle simplement (en tenant
        compte des pièges liés au malagasy) et te donner un conseil de
        prononciation.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    exemple_defaut = "Manger Rakoto du riz avec sa famille hier soir."
    texte_utilisateur = st.text_area(
        "Ton texte à corriger :",
        value="",
        placeholder=f"Exemple : « {exemple_defaut} »",
        height=140,
    )

    colonne_bouton, colonne_info = st.columns([1, 3])
    with colonne_bouton:
        lancer_analyse = st.button("🟢 Analyser ma phrase", use_container_width=True)
    with colonne_info:
        st.caption(
            "Astuce : tu peux coller un paragraphe entier, chaque erreur "
            "importante sera analysée."
        )

    if lancer_analyse:
        if not texte_utilisateur.strip():
            st.error("Merci d'écrire une phrase ou un texte avant de lancer l'analyse.")
        else:
            try:
                with st.spinner("🧠 Analyse en cours par le professeur virtuel..."):
                    prompt_utilisateur = (
                        f"Niveau scolaire de l'élève : {st.session_state.niveau}.\n\n"
                        f"Voici le texte à corriger :\n\"\"\"\n{texte_utilisateur}\n\"\"\""
                    )
                    resultat = appeler_llm(SYSTEM_PROMPT_CORRECTEUR, prompt_utilisateur)

                st.markdown('<div class="mg-card">', unsafe_allow_html=True)
                st.markdown(resultat)
                st.markdown("</div>", unsafe_allow_html=True)

                st.session_state.historique_corrections.insert(
                    0,
                    {
                        "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "texte": texte_utilisateur,
                        "resultat": resultat,
                    },
                )
            except Exception as erreur:
                st.error(f"❌ Une erreur est survenue : {erreur}")

    if st.session_state.historique_corrections:
        with st.expander(
            f"🕓 Historique de mes corrections "
            f"({len(st.session_state.historique_corrections)})"
        ):
            for entree in st.session_state.historique_corrections:
                st.markdown(f"**{entree['date']}** — _{entree['texte']}_")
                st.markdown(entree["resultat"])
                st.divider()
      
# -------------------------------------------------------------------------------------
# ONGLET 2 : STUDIO D'ÉLOCUTION
# -------------------------------------------------------------------------------------
with onglet_elocution:
    st.markdown(
        """
        <div class="mg-card">
        <span class="mg-pill">Phonétique · Prononciation</span>
        <h4>🎙️ Entraîne ton oreille et ta bouche</h4>
        <p style="color:#516059;">
        Écoute la bonne prononciation des sons qui posent le plus de difficulté
        aux apprenants malgaches, puis enregistre-toi pour comparer.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for categorie in SONS_DIFFICILES:
        st.markdown('<div class="mg-sound-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="mg-sound-title">{categorie["titre"]}</div>',
            unsafe_allow_html=True,
        )
        st.write(categorie["explication"])

        colonnes = st.columns(len(categorie["paires_minimales"]))
        for colonne, (mot_a, mot_b) in zip(colonnes, categorie["paires_minimales"]):
            with colonne:
                st.markdown(f"**{mot_a}** / **{mot_b}**")
                cle_bouton = f"ecouter_{categorie['titre']}_{mot_a}_{mot_b}"
                if st.button("🔊 Écouter", key=cle_bouton):
                    try:
                        audio_a = generer_audio(mot_a, lent=True)
                        audio_b = generer_audio(mot_b, lent=True)
                        st.audio(audio_a, format="audio/mp3")
                        st.audio(audio_b, format="audio/mp3")
                    except Exception as erreur:
                        st.error(
                            f"❌ Impossible de générer l'audio (vérifie ta connexion "
                            f"internet) : {erreur}"
                        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="mg-card">
        <h4>🗣️ Phrase d'entraînement personnalisée</h4>
        <p style="color:#516059;">
        Tape une phrase, écoute-la prononcée correctement, puis essaie de la
        répéter en t'enregistrant.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    phrase_entrainement = st.text_input(
        "Phrase à écouter et à répéter :",
        value="Bonjour, je voudrais acheter des bananes et des oranges, s'il vous plaît.",
    )

    col_vitesse_normale, col_vitesse_lente = st.columns(2)
    with col_vitesse_normale:
        if st.button("🔊 Écouter à vitesse normale", use_container_width=True):
            if phrase_entrainement.strip():
                try:
                    audio_normal = generer_audio(phrase_entrainement, lent=False)
                    st.audio(audio_normal, format="audio/mp3")
                except Exception as erreur:
                    st.error(f"❌ Erreur de génération audio : {erreur}")
            else:
                st.warning("Merci d'écrire une phrase.")
    with col_vitesse_lente:
        if st.button("🐢 Écouter au ralenti", use_container_width=True):
            if phrase_entrainement.strip():
                try:
                    audio_lent = generer_audio(phrase_entrainement, lent=True)
                    st.audio(audio_lent, format="audio/mp3")
                except Exception as erreur:
                    st.error(f"❌ Erreur de génération audio : {erreur}")
            else:
                st.warning("Merci d'écrire une phrase.")

    st.markdown("#### 🎤 Enregistre-toi en train de répéter la phrase")
    enregistrement_utilisateur = st.audio_input(
        "Clique pour enregistrer ta prononciation, puis écoute-toi et compare."
    )

    if enregistrement_utilisateur is not None:
        st.audio(enregistrement_utilisateur)
        if st.button("📝 Obtenir un retour sur ma prononciation (transcription IA)"):
            try:
                with st.spinner("🧠 Transcription et analyse en cours..."):
                    octets_audio = enregistrement_utilisateur.getvalue()
                    texte_transcrit = transcrire_audio(octets_audio)

                    prompt_feedback = (
                        f"Niveau scolaire de l'élève : {st.session_state.niveau}.\n"
                        f"Phrase que l'élève devait prononcer : "
                        f"\"{phrase_entrainement}\"\n"
                        f"Voici la transcription de ce que l'élève a réellement "
                        f"prononcé (issue d'une reconnaissance vocale) : "
                        f"\"{texte_transcrit}\"\n\n"
                        f"Compare les deux phrases. Indique les mots ou sons qui ont "
                        f"probablement été mal prononcés (en te basant sur les "
                        f"différences de transcription), donne des conseils "
                        f"articulatoires simples pour les corriger, et encourage "
                        f"l'élève."
                    )
                    retour_prononciation = appeler_llm(
                        SYSTEM_PROMPT_CORRECTEUR, prompt_feedback
                    )

                st.markdown('<div class="mg-card">', unsafe_allow_html=True)
                st.markdown(f"**🎧 Transcription détectée :** _{texte_transcrit}_")
                st.markdown("---")
                st.markdown(retour_prononciation)
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as erreur:
                st.error(f"❌ Une erreur est survenue : {erreur}")
      # -------------------------------------------------------------------------------------
# ONGLET 3 : MISE EN SITUATION
# -------------------------------------------------------------------------------------
with onglet_situation:
    st.markdown(
        """
        <div class="mg-card">
        <span class="mg-pill">Dialogues · Vie quotidienne</span>
        <h4>🎭 Génère un dialogue adapté à ton quotidien</h4>
        <p style="color:#516059;">
        Choisis une situation courante à Madagascar : notre professeur virtuel va
        créer un dialogue réaliste, avec du vocabulaire clé et un point de
        grammaire expliqué.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scenario_choisi = st.selectbox(
        "📍 Choisis une situation du quotidien :", options=SCENARIOS_DIALOGUE
    )

    scenario_personnalise = st.text_input(
        "Ou décris ta propre situation (optionnel) :",
        placeholder="Exemple : demander son chemin dans la ville d'Antsirabe",
    )

    if st.button("🎬 Générer le dialogue", use_container_width=False):
        situation_finale = (
            scenario_personnalise.strip() if scenario_personnalise.strip() else scenario_choisi
        )
        try:
            with st.spinner("✍️ Rédaction du dialogue en cours..."):
                prompt_dialogue = (
                    f"Niveau scolaire de l'élève : {st.session_state.niveau}.\n"
                    f"Situation demandée : {situation_finale}.\n\n"
                    f"Génère le dialogue en respectant scrupuleusement les "
                    f"consignes de ton prompt système."
                )
                dialogue_genere = appeler_llm(SYSTEM_PROMPT_DIALOGUE, prompt_dialogue)

            st.markdown('<div class="mg-card">', unsafe_allow_html=True)
            st.markdown(dialogue_genere)
            st.markdown("</div>", unsafe_allow_html=True)

            try:
                audio_dialogue = generer_audio(dialogue_genere.replace("*", "").replace("#", ""))
                st.markdown("**🔊 Écouter une lecture du dialogue :**")
                st.audio(audio_dialogue, format="audio/mp3")
            except Exception:
                st.info(
                    "ℹ️ La lecture audio automatique n'a pas pu être générée pour "
                    "ce dialogue, mais tu peux toujours le lire ci-dessus."
                )

            st.session_state.historique_dialogues.insert(
                0,
                {
                    "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "situation": situation_finale,
                    "dialogue": dialogue_genere,
                },
            )
        except Exception as erreur:
            st.error(f"❌ Une erreur est survenue : {erreur}")

    if st.session_state.historique_dialogues:
        with st.expander(
            f"🕓 Historique de mes dialogues "
            f"({len(st.session_state.historique_dialogues)})"
        ):
            for entree in st.session_state.historique_dialogues:
                st.markdown(f"**{entree['date']}** — _{entree['situation']}_")
                st.markdown(entree["dialogue"])
                st.divider()

# =====================================================================================
# 10. PIED DE PAGE
# =====================================================================================

st.markdown(
    """
    <div class="mg-footer">
    🇲🇬 FrançaisPro Madagascar — Conçu avec bienveillance pour accompagner chaque
    élève et étudiant malgache vers la réussite en français. 💚
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================================
# 11. INSTRUCTIONS D'INSTALLATION ET DE LANCEMENT
# =====================================================================================
#
# 1) Crée un environnement virtuel (recommandé) :
#       python -m venv venv
#       source venv/bin/activate        (sous Linux/Mac)
#       venv\\Scripts\\activate           (sous Windows)
#
# 2) Installe les dépendances nécessaires :
#       pip install streamlit openai google-generativeai gTTS
#
# 3) Lance l'application depuis le dossier contenant ce fichier :
#       streamlit run app.py
#
# 4) Une fois l'application ouverte dans le navigateur :
#       - Ouvre la barre latérale (⚙️ Configuration)
#       - Choisis ton fournisseur d'IA (OpenAI ou Google Gemini)
#       - Colle ta clé API personnelle (obtenue sur platform.openai.com ou
#         aistudio.google.com)
#       - Choisis le niveau scolaire de l'élève (Collège, Lycée, Université)
#       - Utilise les 3 onglets : Correcteur & Structure, Studio d'Élocution,
#         Mise en Situation.
#
# Remarque : la fonctionnalité d'enregistrement audio (st.audio_input) nécessite
# une version récente de Streamlit (>= 1.35). Mets à jour Streamlit si besoin :
#       pip install --upgrade streamlit
#
# =====================================================================================
