"""
app.py — Application Streamlit : Analyse des arrêtés préfectoraux éoliens
=========================================================================
Point d'entrée de l'application web. Lance : streamlit run app.py
"""

import streamlit as st

# ── Configuration de la page (doit être le premier appel Streamlit) ──────────
st.set_page_config(
    page_title="DREAL Éolien — Analyse environnementale",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Injection du CSS personnalisé ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ══════════════════════════════════════════════════
   PALETTE — fond blanc pur, encre foncée, accents nets
   ══════════════════════════════════════════════════ */
:root {
  --blanc:      #FFFFFF;
  --fond:       #F8F9FA;
  --encre:      #111827;
  --encre-mid:  #374151;
  --gris:       #6B7280;
  --gris-clair: #E5E7EB;
  --bordure:    #D1D5DB;

  --vert:       #166534;
  --vert-mid:   #15803D;
  --vert-fond:  #F0FDF4;
  --vert-bord:  #BBF7D0;

  /* Couleurs thématiques — saturées, lisibles sur fond blanc */
  --avi:   #1D4ED8;   /* bleu vif       — avifaune    */
  --chi:   #7C3AED;   /* violet         — chiroptères */
  --hum:   #0F766E;   /* teal           — zones humides */
  --pay:   #C2410C;   /* orange brûlé   — paysage     */

  /* Fonds surlignés pour les mots-clés (très pâles) */
  --avi-hl:  #DBEAFE;
  --chi-hl:  #EDE9FE;
  --hum-hl:  #CCFBF1;
  --pay-hl:  #FFEDD5;
}

/* ══════════════════════════════════════════════════
   BASE — police et fond
   ══════════════════════════════════════════════════ */
html, body, [class*="css"] {
  font-family: 'DM Sans', system-ui, sans-serif !important;
  background-color: var(--fond) !important;
  color: var(--encre) !important;
  font-size: 15px;
  line-height: 1.6;
}

/* ══════════════════════════════════════════════════
   EN-TÊTE
   ══════════════════════════════════════════════════ */
.entete {
  background: var(--vert);
  color: white;
  padding: 2rem 2.5rem 1.8rem;
  margin: -1rem -1rem 2rem -1rem;
  border-bottom: 3px solid var(--vert-mid);
}
.entete h1 {
  font-family: 'DM Serif Display', Georgia, serif !important;
  font-weight: 400;
  font-size: 1.9rem;
  letter-spacing: -0.01em;
  margin: 0 0 0.35rem;
  line-height: 1.25;
  color: white !important;
}
.entete p {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.92rem;
  opacity: 0.82;
  margin: 0;
  color: white !important;
}

/* ══════════════════════════════════════════════════
   CARTE D'EXTRAIT  — cœur de l'interface
   ══════════════════════════════════════════════════ */
.extrait-card {
  background: var(--blanc);
  border: 1px solid var(--bordure);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  transition: box-shadow 0.15s;
}
.extrait-card:hover {
  box-shadow: 0 3px 10px rgba(0,0,0,0.11);
}

/* Bande colorée gauche selon thème dominant */
.extrait-card.th-avifaune  { border-left: 4px solid var(--avi); }
.extrait-card.th-chiropteres { border-left: 4px solid var(--chi); }
.extrait-card.th-zones_humides { border-left: 4px solid var(--hum); }
.extrait-card.th-paysage   { border-left: 4px solid var(--pay); }

/* En-tête de la carte */
.ec-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 8px;
  border-bottom: 1px solid var(--gris-clair);
  flex-wrap: wrap;
}

/* Référence d'article */
.ec-art {
  font-family: 'DM Mono', monospace;
  font-size: 0.76rem;
  font-weight: 500;
  color: var(--encre-mid);
  background: var(--fond);
  border: 1px solid var(--bordure);
  border-radius: 4px;
  padding: 2px 8px;
  white-space: nowrap;
}

/* Badge thème */
.ec-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  padding: 2px 9px;
  border-radius: 20px;
  color: white;
  white-space: nowrap;
}
.ec-badge.avi { background: var(--avi); }
.ec-badge.chi { background: var(--chi); }
.ec-badge.hum { background: var(--hum); }
.ec-badge.pay { background: var(--pay); }

/* Score */
.ec-score {
  margin-left: auto;
  font-family: 'DM Mono', monospace;
  font-size: 0.72rem;
  color: var(--gris);
  white-space: nowrap;
}
.ec-score span {
  font-weight: 600;
  color: var(--encre-mid);
}

/* Corps de la carte — texte extrait */
.ec-body {
  padding: 10px 14px 12px;
}

/* Conteneur du texte avec limitation à 5 lignes */
.ec-text-wrap {
  position: relative;
}
.ec-text {
  font-family: 'DM Sans', sans-serif;
  font-size: 0.895rem;
  line-height: 1.7;
  color: var(--encre);
  /* 5 lignes exactement : line-height 1.7 × 0.895rem × 5 */
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}
.ec-text.expanded {
  display: block;
  -webkit-line-clamp: unset;
  overflow: visible;
}

/* Bouton "Voir plus / Voir moins" */
.ec-toggle {
  display: inline-block;
  margin-top: 5px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--vert-mid);
  cursor: pointer;
  text-decoration: none;
  background: none;
  border: none;
  padding: 0;
}
.ec-toggle:hover { text-decoration: underline; }

/* Surlignage des mots-clés dans le texte */
.hl-avi  { background: var(--avi-hl);  border-radius: 2px; padding: 0 2px; }
.hl-chi  { background: var(--chi-hl);  border-radius: 2px; padding: 0 2px; }
.hl-hum  { background: var(--hum-hl);  border-radius: 2px; padding: 0 2px; }
.hl-pay  { background: var(--pay-hl);  border-radius: 2px; padding: 0 2px; }

/* En-tête de document */
.doc-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin: 20px 0 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--vert-bord);
}
.doc-header .doc-title {
  font-family: 'DM Serif Display', serif;
  font-size: 1.05rem;
  color: var(--vert);
  font-weight: 400;
}
.doc-header .doc-meta {
  font-size: 0.78rem;
  color: var(--gris);
  font-family: 'DM Mono', monospace;
}

/* ══════════════════════════════════════════════════
   NOTE MÉTHODOLOGIQUE
   ══════════════════════════════════════════════════ */
.note-methodo {
  background: var(--vert-fond);
  border: 1px solid var(--vert-bord);
  border-left: 4px solid var(--vert-mid);
  border-radius: 6px;
  padding: 0.8rem 1.1rem;
  font-size: 0.84rem;
  color: var(--vert);
  margin-bottom: 1.4rem;
}

/* ══════════════════════════════════════════════════
   BARRES DE PROGRESSION
   ══════════════════════════════════════════════════ */
.barre-theme {
  display: flex; align-items: center; gap: 10px; margin-bottom: 7px;
}
.barre-theme .nom {
  font-size: 0.82rem; font-weight: 600; width: 115px; color: var(--encre-mid);
}
.barre-theme .piste {
  flex: 1; background: var(--gris-clair); border-radius: 3px; height: 7px; overflow: hidden;
}
.barre-theme .rempli { height: 7px; border-radius: 3px; }
.barre-theme .val {
  font-family: 'DM Mono', monospace; font-size: 0.78rem; color: var(--gris); width: 32px; text-align: right;
}

/* ══════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: #1A2E1F !important;
}
[data-testid="stSidebar"] * { color: #E8F5E9 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }

/* Champ de sélection — fond légèrement clair */
[data-testid="stSidebar"] .stSelectbox > div,
[data-testid="stSidebar"] .stMultiSelect > div {
  background: rgba(255,255,255,0.08) !important;
  border-color: rgba(255,255,255,0.2) !important;
}

/* Listes déroulantes (portail hors sidebar, fond blanc) — texte noir lisible */
[data-baseweb="popover"] *,
[data-baseweb="menu"] *,
[data-baseweb="select"] [role="listbox"] *,
ul[role="listbox"] *,
li[role="option"] {
  color: #111827 !important;
  background-color: white !important;
}
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
  background-color: #F0FDF4 !important;
  color: #166534 !important;
}

/* ══════════════════════════════════════════════════
   BOUTONS
   ══════════════════════════════════════════════════ */
.stButton > button {
  background: var(--vert) !important;
  color: white !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  border: none !important;
  border-radius: 6px !important;
  padding: 0.45rem 1.3rem !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.01em !important;
}
.stButton > button:hover { background: var(--vert-mid) !important; }

.stDownloadButton > button {
  background: white !important;
  color: var(--vert) !important;
  border: 1.5px solid var(--vert) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
}

/* ══════════════════════════════════════════════════
   MÉTRIQUES & ONGLETS
   ══════════════════════════════════════════════════ */
[data-testid="metric-container"] {
  background: var(--blanc);
  border: 1px solid var(--bordure);
  border-radius: 8px;
  padding: 1rem 1.1rem;
}
[data-testid="metric-container"] label {
  font-size: 0.78rem !important;
  color: var(--gris) !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: 'DM Serif Display', serif !important;
  font-size: 2rem !important;
  color: var(--encre) !important;
}

.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 2px solid var(--gris-clair) !important; }
.stTabs [data-baseweb="tab"] {
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.86rem !important;
  color: var(--gris) !important;
  padding: 8px 16px !important;
  border-radius: 6px 6px 0 0 !important;
}
.stTabs [aria-selected="true"] {
  color: var(--vert) !important;
  border-bottom: 2px solid var(--vert) !important;
}

h2, h3 {
  font-family: 'DM Serif Display', Georgia, serif !important;
  font-weight: 400 !important;
  color: var(--encre) !important;
}

/* Upload zone */
[data-testid="stFileUploader"] {
  background: var(--blanc) !important;
  border: 2px dashed var(--bordure) !important;
  border-radius: 8px !important;
}

/* ══════════════════════════════════════════════════
   EXPAND / COLLAPSE — mécanisme CSS pur via <details>
   Le JS de Streamlit est bloqué par le navigateur ;
   on utilise l'élément natif HTML5 <details>/<summary>
   qui fonctionne sans aucun script.
   ══════════════════════════════════════════════════ */

/* Conteneur dépliable */
.ec-details {
  margin: 0;
  padding: 0;
}

/* Le texte tronqué à 5 lignes est dans le <summary> */
.ec-details summary {
  list-style: none;        /* masquer le triangle natif */
  cursor: pointer;
  outline: none;
}
.ec-details summary::-webkit-details-marker { display: none; }

/* Texte limité à 5 lignes quand replié */
.ec-details:not([open]) .ec-text {
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Texte complet quand déplié */
.ec-details[open] .ec-text {
  display: block;
  overflow: visible;
}

/* Bouton textuel sous le texte */
.ec-details summary .ec-toggle-label {
  display: inline-block;
  margin-top: 5px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--vert-mid);
  text-decoration: none;
}
.ec-details summary .ec-toggle-label::after {
  content: "▼ Voir tout";
}
.ec-details[open] summary .ec-toggle-label::after {
  content: "▲ Réduire";
}
</style>
""", unsafe_allow_html=True)

# ── Imports après configuration ────────────────────────────────────────────────
import os, sys, json, io, tempfile, zipfile
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from core.extractor import parse_arrete_from_bytes, THEMES_FR
from core.reporter import build_aggregation, build_summary_table, build_html_report

# ── État de session ────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []
if "analysed" not in st.session_state:
    st.session_state.analysed = False

# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="entete">
  <h1>🌬️ DREAL Éolien · Analyse environnementale</h1>
  <p>Extraction automatisée des prescriptions environnementales dans les arrêtés préfectoraux éoliens</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Paramètres et chargement
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")
    st.markdown("---")

    region_choisie = st.selectbox(
        "Région administrative",
        options=[
            "Autre / Non spécifiée",
            "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne",
            "Centre-Val-de-Loire", "Grand-Est", "Hauts-de-France",
            "Île-de-France", "Normandie", "Nouvelle-Aquitaine",
            "Occitanie", "Pays-de-la-Loire", "Provence-Alpes-Côte-d'Azur",
        ],
        index=0,
        help="Associée aux PDFs que vous allez déposer."
    )

    annee = st.text_input("Année (optionnel)", placeholder="ex : 2023",
                          help="Si non renseignée, elle sera extraite du nom du fichier.")

    mois_options = {
        "": "— Non spécifié —", "01": "Janvier", "02": "Février",
        "03": "Mars", "04": "Avril", "05": "Mai", "06": "Juin",
        "07": "Juillet", "08": "Août", "09": "Septembre",
        "10": "Octobre", "11": "Novembre", "12": "Décembre",
    }
    mois = st.selectbox("Mois (optionnel)", options=list(mois_options.keys()),
                        format_func=lambda k: mois_options[k])

    st.markdown("---")
    st.markdown("### 🎯 Thèmes à rechercher")
    themes_actifs = st.multiselect(
        "Sélectionnez les thématiques",
        options=list(THEMES_FR.keys()),
        default=list(THEMES_FR.keys()),
        format_func=lambda k: THEMES_FR[k],
    )

    st.markdown("---")
    st.markdown("### 📋 À propos")
    st.markdown("""
<span style='font-size:0.82rem; opacity:0.8'>
Outil d'extraction automatisée des prescriptions environnementales
(avifaune, chiroptères, zones humides, paysage) dans les arrêtés
préfectoraux éoliens publiés par les DREAL.

**Classification** : mots-clés pondérés (forts = 2 pts, faibles = 1 pt).
Seuil minimal : 2 points par passage.
</span>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ZONE DE DÉPÔT DES PDFS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📂 Déposez vos arrêtés préfectoraux")

col_upload, col_demo = st.columns([3, 1])

with col_upload:
    uploaded_files = st.file_uploader(
        "Glissez-déposez vos PDFs ici (plusieurs fichiers acceptés)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Les PDFs doivent être nativement numériques (texte extractible). "
             "Les PDFs scannés nécessitent un OCR préalable."
    )

with col_demo:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎭 Charger la démo", use_container_width=True,
                 help="Charge des données simulées représentatives pour explorer l'interface"):
        # Charger les données de démonstration intégrées
        from core.demo_data import DEMO_RESULTS
        st.session_state.results = DEMO_RESULTS
        st.session_state.analysed = True
        st.success(f"✓ Démo chargée — {len(DEMO_RESULTS)} arrêtés simulés")

# ── Bouton d'analyse ───────────────────────────────────────────────────────────
if uploaded_files:
    n = len(uploaded_files)
    st.markdown(f"**{n} fichier(s) sélectionné(s)** — Cliquez sur Analyser pour lancer le traitement.")

    if st.button(f"🔍 Analyser {n} arrêté(s)", type="primary", use_container_width=False):
        progress = st.progress(0, text="Initialisation...")
        results = []
        errors = []

        for i, f in enumerate(uploaded_files):
            progress.progress((i) / n, text=f"Traitement : {f.name} ({i+1}/{n})")
            # CORRECTIF CURSEUR : on lit les bytes UNE SEULE FOIS ici et on les
            # stocke dans une variable locale immuable (bytes). L'objet f de type
            # UploadedFile possède un curseur interne — tout appel ultérieur à
            # f.read() retournerait 0 bytes. Toute la suite travaille sur pdf_bytes.
            f.seek(0)        # repositionner au cas où Streamlit aurait déjà lu partiellement
            pdf_bytes = f.read()  # lecture unique et définitive

            # Extraire date depuis le nom du fichier si non fournie
            from core.extractor import extract_date_from_filename
            date_info = extract_date_from_filename(f.name)

            metadata = {
                "url": "",
                "text": f.name,
                "region": region_choisie,
                "year": annee if annee else date_info.get("year"),
                "month": mois if mois else date_info.get("month"),
                "downloaded": True,
                "local_path": f.name,
                "filename": f.name,
            }

            result = parse_arrete_from_bytes(pdf_bytes, metadata, themes_actifs)
            results.append(result)

            if not result["extraction_ok"]:
                errors.append(f.name)

        progress.progress(1.0, text="✓ Analyse terminée")
        st.session_state.results = results
        st.session_state.analysed = True

        if errors:
            st.warning(
                f"⚠️ {len(errors)} fichier(s) non extractibles (PDFs scannés ?) : "
                + ", ".join(errors)
            )

# ══════════════════════════════════════════════════════════════════════════════
# RÉSULTATS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.analysed and st.session_state.results:
    results = st.session_state.results
    results_ok = [r for r in results if r.get("extraction_ok")]

    st.markdown("---")
    st.markdown("## 📊 Résultats de l'analyse")

    # ── Métadonnées globales ───────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    total_passages = sum(len(r.get("passages", [])) for r in results_ok)
    docs_failed = len(results) - len(results_ok)

    with col1:
        st.metric("Arrêtés analysés", len(results_ok),
                  delta=f"-{docs_failed} non extractibles" if docs_failed else None,
                  delta_color="inverse")
    with col2:
        st.metric("Passages thématiques", total_passages)

    # Comptage par thème
    theme_counts = defaultdict(int)
    for r in results_ok:
        for th in r.get("themes_found", []):
            theme_counts[th] += 1

    with col3:
        top_theme = max(theme_counts, key=theme_counts.get) if theme_counts else "—"
        st.metric("Thème dominant", THEMES_FR.get(top_theme, top_theme))
    with col4:
        regions = set(r.get("region") for r in results_ok)
        st.metric("Régions couvertes", len(regions))

    # ── Barres thématiques ─────────────────────────────────────────────────
    if theme_counts and len(results_ok) > 0:
        st.markdown("**Couverture par thématique** (nombre d'arrêtés concernés)")
        colors = {"avifaune": "#1565C0", "chiropteres": "#6A1B9A",
                  "zones_humides": "#00695C", "paysage": "#E65100"}
        max_val = max(theme_counts.values())
        barre_html = ""
        for th_key, th_label in THEMES_FR.items():
            val = theme_counts.get(th_key, 0)
            pct = int(100 * val / max_val) if max_val else 0
            c = colors.get(th_key, "#888")
            barre_html += f"""
            <div class="barre-theme">
              <span class="nom">{th_label}</span>
              <div class="piste"><div class="rempli" style="width:{pct}%;background:{c}"></div></div>
              <span class="val">{val}</span>
            </div>"""
        st.markdown(barre_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Onglets principaux ────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📖 Extraits par thème", "📋 Tableau de synthèse", "📥 Exports"])

    # ════════ TAB 1 : EXTRAITS ════════════════════════════════════════════
    with tab1:
        st.markdown("""
        <div class="note-methodo">
          Les extraits ci-dessous sont classifiés automatiquement par un système de mots-clés pondérés.
          Chaque passage est accompagné d'un score de pertinence. Un score élevé indique une forte
          concentration de termes spécifiques à la thématique.
        </div>
        """, unsafe_allow_html=True)

        # Filtres d'affichage
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            theme_filtre = st.selectbox(
                "Filtrer par thème",
                options=["Tous"] + list(THEMES_FR.keys()),
                format_func=lambda k: "— Tous les thèmes —" if k == "Tous" else THEMES_FR.get(k, k)
            )
        with col_f2:
            region_filtre = st.selectbox(
                "Filtrer par région",
                options=["Toutes"] + sorted(set(r.get("region","") for r in results_ok))
            )

        # ── Fonctions utilitaires pour le rendu ──────────────────────────────
        icons      = {"avifaune": "🦅", "chiropteres": "🦇",
                      "zones_humides": "💧", "paysage": "🌄"}
        badge_cls  = {"avifaune": "avi", "chiropteres": "chi",
                      "zones_humides": "hum", "paysage": "pay"}
        hl_cls     = {"avifaune": "hl-avi", "chiropteres": "hl-chi",
                      "zones_humides": "hl-hum", "paysage": "hl-pay"}
        th_cls     = {"avifaune": "th-avifaune", "chiropteres": "th-chiropteres",
                      "zones_humides": "th-zones_humides", "paysage": "th-paysage"}

        # Mots-clés forts normalisés, pour le surlignage dans le texte
        from core.extractor import THEMES, normalize as norm_kw

        def highlight_keywords(text: str, themes_scores: dict) -> str:
            """
            Surligne dans le texte les mots-clés des thèmes détectés.
            On surligne uniquement les mots-clés FORTS du thème dominant
            (les faibles sont partagés entre thèmes et créeraient de la confusion).
            Le surlignage est insensible à la casse et aux accents.
            """
            import re as _re
            result = text
            dom = max(themes_scores, key=themes_scores.get) if themes_scores else None
            if not dom:
                return result

            cls = hl_cls.get(dom, "")
            # Trier par longueur décroissante pour surligner d'abord les expressions
            # longues (évite de surligner "milan" dans "milan royal" partiellement)
            kws = sorted(THEMES[dom]["strong"], key=len, reverse=True)

            for kw in kws:
                # Regex insensible à la casse, frontière de mot
                pattern = _re.compile(
                    r'(?<![&;])(' + _re.escape(kw) + r')',
                    _re.IGNORECASE
                )
                # On ne surligne que si le mot-clé apparaît dans le texte
                if pattern.search(result):
                    result = pattern.sub(
                        rf'<mark class="{cls}">\1</mark>',
                        result,
                        count=5   # limiter à 5 occurrences max par mot-clé
                    )
            return result

        # ── Rendu des extraits ────────────────────────────────────────────────
        # Architecture hybride :
        #   - En-tête de document + bandeau badges/score → HTML via st.markdown()
        #   - Texte de l'extrait → st.expander() natif Streamlit (seul moyen
        #     fiable d'avoir un vrai expand/collapse, le JS étant bloqué)
        passages_affiches = 0

        for doc in results_ok:
            if region_filtre != "Toutes" and doc.get("region") != region_filtre:
                continue

            doc_passages = [
                p for p in doc.get("passages", [])
                if (theme_filtre == "Tous" or theme_filtre in p.get("themes", {}))
            ]
            if not doc_passages:
                continue

            # En-tête du document
            date_str = (
                "{}/{}".format(doc.get("month", "?"), doc.get("year", "?"))
                if doc.get("year") else "date inconnue"
            )
            titre  = (doc.get("text") or doc.get("filename") or "")[:90]
            region = (doc.get("region") or "")
            st.markdown(
                '<div class="doc-header">'
                '<span class="doc-title">&#128196; {t}</span>'
                '<span class="doc-meta">{r} &middot; {d}</span>'
                '</div>'.format(
                    t=titre.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"),
                    r=region,
                    d=date_str,
                ),
                unsafe_allow_html=True,
            )

            for p in doc_passages[:15]:
                dom    = p.get("dominant_theme", "")
                themes = p.get("themes", {})
                score  = themes.get(dom, 0)

                # ── Bandeau badges + score (HTML) ────────────────────────────
                badges_html = "".join(
                    '<span class="ec-badge {cls}">{ico} {lbl}</span> '.format(
                        cls=badge_cls.get(th, ""),
                        ico=icons.get(th, ""),
                        lbl=THEMES_FR.get(th, th),
                    )
                    for th in themes
                )
                art_html = (
                    '<span class="ec-art">{}</span> '.format(
                        p["article_ref"]
                        .replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                    )
                    if p.get("article_ref") else ""
                )
                score_stars = "&#9679;" * min(score // 4 + 1, 5)

                st.markdown(
                    '<div class="ec-header" style="'
                    'display:flex;align-items:center;gap:8px;flex-wrap:wrap;'
                    'padding:8px 12px;background:white;'
                    'border:1px solid #D1D5DB;border-radius:8px 8px 0 0;'
                    'border-left:4px solid {color};margin-bottom:0;">'
                    '{art}{badges}'
                    '<span class="ec-score" style="margin-left:auto;">'
                    'Score <span style="font-weight:600;">{score}</span> {stars}'
                    '</span>'
                    '</div>'.format(
                        color={"avifaune":"#1D4ED8","chiropteres":"#7C3AED",
                               "zones_humides":"#0F766E","paysage":"#C2410C"}.get(dom,"#9CA3AF"),
                        art=art_html,
                        badges=badges_html,
                        score=score,
                        stars=score_stars,
                    ),
                    unsafe_allow_html=True,
                )

                # ── Texte via st.expander (expand/collapse natif) ────────────
                raw_text = (p.get("text") or "")

                # Aperçu : 5 premières lignes affichées hors expander
                lignes    = raw_text.splitlines()
                apercu    = "\n".join(lignes[:5])
                a_suite   = len(lignes) > 5

                # Surlignage des mots-clés dans l'aperçu (texte brut Markdown)
                def bold_keywords(txt: str, th_scores: dict) -> str:
                    import re as _re
                    if not th_scores:
                        return txt
                    d = max(th_scores, key=th_scores.get)
                    for kw in sorted(THEMES[d]["strong"], key=len, reverse=True):
                        pat = _re.compile(r'(?<!\*\*)(' + _re.escape(kw) + r')(?!\*\*)',
                                          _re.IGNORECASE)
                        if pat.search(txt):
                            txt = pat.sub(r'**\1**', txt, count=3)
                    return txt

                # Conteneur avec bordure basse arrondie pour raccorder à l'en-tête
                with st.container():
                    st.markdown(
                        '<div style="border:1px solid #D1D5DB;border-top:none;'
                        'border-radius:0 0 8px 8px;padding:10px 14px 6px;'
                        'background:white;margin-bottom:12px;">',
                        unsafe_allow_html=True,
                    )
                    # Aperçu 5 lignes toujours visible
                    st.markdown(bold_keywords(apercu, themes))

                    # Ligne basse : "Voir tout" + bouton Copier côte à côte
                    col_exp, col_copy = st.columns([4, 1])

                    with col_exp:
                        if a_suite:
                            with st.expander("Voir tout l'extrait"):
                                st.markdown(bold_keywords(raw_text, themes))

                    with col_copy:
                        # Bouton copier via st.components — le seul moyen d'exécuter
                        # du JS réel dans Streamlit (navigator.clipboard.writeText)
                        # On échappe le texte pour l'insérer dans un littéral JS
                        texte_js = (raw_text
                                    .replace("\\", "\\\\")
                                    .replace("`", "\\`")
                                    .replace("$", "\\$"))
                        import streamlit.components.v1 as components
                        components.html(
                            """
                            <style>
                              button {
                                width: 100%;
                                padding: 5px 10px;
                                font-size: 12px;
                                font-family: 'DM Sans', sans-serif;
                                font-weight: 600;
                                color: #166534;
                                background: white;
                                border: 1.5px solid #166534;
                                border-radius: 6px;
                                cursor: pointer;
                                transition: background 0.15s;
                              }
                              button:hover { background: #F0FDF4; }
                              button.copied {
                                color: white;
                                background: #166534;
                                border-color: #166534;
                              }
                            </style>
                            <button id="btn" onclick="copyText()">📋 Copier</button>
                            <script>
                              function copyText() {
                                const txt = `""" + texte_js + """`;
                                navigator.clipboard.writeText(txt).then(function() {
                                  const btn = document.getElementById('btn');
                                  btn.textContent = '✓ Copié !';
                                  btn.classList.add('copied');
                                  setTimeout(function() {
                                    btn.textContent = '📋 Copier';
                                    btn.classList.remove('copied');
                                  }, 2000);
                                });
                              }
                            </script>
                            """,
                            height=38,
                        )

                    st.markdown('</div>', unsafe_allow_html=True)

                passages_affiches += 1

        if passages_affiches == 0:
            st.info("Aucun passage ne correspond aux filtres sélectionnés.")

    # ════════ TAB 2 : TABLEAU DE SYNTHÈSE ════════════════════════════════
    with tab2:
        import pandas as pd

        agg = build_aggregation(results_ok)
        rows = build_summary_table(agg)

        if rows:
            df = pd.DataFrame(rows)
            # Retirer la colonne technique Mois_num
            if "Mois_num" in df.columns:
                df = df.drop(columns=["Mois_num"])

            # Filtres sur le tableau
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                reg_filter = st.multiselect(
                    "Régions à afficher",
                    options=sorted(df["Région"].unique()),
                    default=sorted(df["Région"].unique())
                )
            with col_t2:
                years = sorted(df["Année"].unique())
                year_filter = st.multiselect("Années", options=years, default=years)

            df_filtered = df[df["Région"].isin(reg_filter) & df["Année"].isin(year_filter)]

            # Mise en forme conditionnelle
            theme_cols = [THEMES_FR[k] for k in THEMES_FR]

            def colorize(val):
                if not isinstance(val, (int, float)) or val == 0:
                    return ""
                intensity = min(int(255 - (val / max(df_filtered[theme_cols].max()) * 120)), 245)
                return f"background-color: rgb({intensity}, 230, {intensity}); color: #1A1A1A"

            styled = df_filtered.style.applymap(colorize, subset=theme_cols)
            st.dataframe(styled, use_container_width=True, height=400)

            st.caption(f"💡 {len(df_filtered)} ligne(s) · coloration proportionnelle au nombre de passages détectés")
        else:
            st.info("Aucune donnée à afficher.")

    # ════════ TAB 3 : EXPORTS ══════════════════════════════════════════════
    with tab3:
        st.markdown("### 📥 Télécharger les résultats")
        st.markdown("Trois formats disponibles selon votre usage :")

        agg = build_aggregation(results_ok)
        rows = build_summary_table(agg)

        col_e1, col_e2, col_e3 = st.columns(3)

        # ── Export CSV ──
        with col_e1:
            st.markdown("**Tableau CSV**")
            st.markdown("Compatible Excel / LibreOffice. Une ligne par région × mois × thème.")
            if rows:
                import csv, io as sio
                buf = sio.StringIO()
                writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), delimiter=";")
                writer.writeheader()
                writer.writerows(rows)
                st.download_button(
                    "⬇️ Télécharger CSV",
                    data=buf.getvalue().encode("utf-8-sig"),
                    file_name="synthese_arrete_eolien.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # ── Export HTML ──
        with col_e2:
            st.markdown("**Rapport HTML**")
            st.markdown("Rapport interactif navigable, avec extraits complets et filtres.")
            html_content = build_html_report(agg, rows, results_ok)
            st.download_button(
                "⬇️ Télécharger HTML",
                data=html_content.encode("utf-8"),
                file_name="rapport_arrete_eolien.html",
                mime="text/html",
                use_container_width=True
            )

        # ── Export JSON ──
        with col_e3:
            st.markdown("**Données JSON**")
            st.markdown("Export brut avec tous les extraits et métadonnées pour traitement externe.")
            json_data = json.dumps(agg, ensure_ascii=False, indent=2)
            st.download_button(
                "⬇️ Télécharger JSON",
                data=json_data.encode("utf-8"),
                file_name="synthese_arrete_eolien.json",
                mime="application/json",
                use_container_width=True
            )

        # ── Réinitialiser ──
        st.markdown("---")
        if st.button("🗑️ Effacer l'analyse et recommencer"):
            st.session_state.results = []
            st.session_state.analysed = False
            st.rerun()
