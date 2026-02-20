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
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap');

/* ── Palette & variables ── */
:root {
  --vert:     #1B4D3E;
  --vert-mid: #2D7A5F;
  --vert-clair: #A8D5C2;
  --creme:    #F7F4EE;
  --encre:    #1A1A1A;
  --gris:     #6B6B6B;
  --bordure:  #D8D3C8;
  --avifaune:  #1565C0;
  --chiro:     #6A1B9A;
  --humides:   #00695C;
  --paysage:   #E65100;
}

/* ── Reset & base ── */
html, body, [class*="css"] {
  font-family: 'Source Serif 4', Georgia, serif;
  background-color: var(--creme) !important;
  color: var(--encre);
}

/* ── En-tête principal ── */
.entete {
  background: var(--vert);
  color: white;
  padding: 2.5rem 3rem 2rem;
  margin: -1rem -1rem 2rem -1rem;
  border-bottom: 4px solid var(--vert-mid);
}
.entete h1 {
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: 2.1rem;
  letter-spacing: -0.02em;
  margin: 0 0 0.4rem;
  line-height: 1.2;
}
.entete p {
  font-family: 'Source Serif 4', serif;
  font-style: italic;
  font-weight: 300;
  font-size: 1.05rem;
  opacity: 0.85;
  margin: 0;
}

/* ── Cartes thématiques ── */
.carte-theme {
  border-radius: 10px;
  padding: 1.1rem 1.3rem;
  margin-bottom: 0.8rem;
  border-left: 5px solid;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.carte-avifaune  { border-color: var(--avifaune); }
.carte-chiro     { border-color: var(--chiro); }
.carte-humides   { border-color: var(--humides); }
.carte-paysage   { border-color: var(--paysage); }

.carte-theme .label {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 0.2rem;
}
.carte-theme .chiffre {
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: 2rem;
  line-height: 1;
}
.carte-theme .sous {
  font-size: 0.82rem;
  font-style: italic;
  color: var(--gris);
  margin-top: 0.15rem;
}

/* ── Carte d'extrait ── */
.extrait-card {
  background: white;
  border: 1px solid var(--bordure);
  border-radius: 10px;
  padding: 1.2rem 1.4rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.extrait-card .meta {
  font-family: 'Syne', sans-serif;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--gris);
  margin-bottom: 0.6rem;
}
.extrait-card .article-tag {
  display: inline-block;
  background: var(--creme);
  border: 1px solid var(--bordure);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 0.8rem;
  font-family: 'Syne', sans-serif;
  font-weight: 600;
  margin-right: 6px;
}
.extrait-card blockquote {
  border-left: 3px solid var(--vert-clair);
  margin: 0.5rem 0 0;
  padding-left: 1rem;
  font-style: italic;
  font-size: 0.9rem;
  line-height: 1.65;
  color: #333;
}
.score-pill {
  display: inline-block;
  background: var(--creme);
  border: 1px solid var(--bordure);
  border-radius: 20px;
  padding: 1px 10px;
  font-size: 0.75rem;
  font-family: 'Syne', sans-serif;
  color: var(--gris);
  float: right;
}

/* ── Badge de thème ── */
.badge { display: inline-block; border-radius: 20px; padding: 2px 10px;
         font-size: 0.75rem; font-family: 'Syne', sans-serif; font-weight: 700;
         letter-spacing: 0.04em; color: white; margin-right: 4px; }
.badge-avifaune  { background: var(--avifaune); }
.badge-chiro     { background: var(--chiro); }
.badge-humides   { background: var(--humides); }
.badge-paysage   { background: var(--paysage); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--vert) !important;
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2) !important; }

/* ── Boutons ── */
.stButton > button {
  background: var(--vert) !important;
  color: white !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: 0.04em !important;
  border: none !important;
  border-radius: 6px !important;
  padding: 0.5rem 1.5rem !important;
}
.stButton > button:hover { background: var(--vert-mid) !important; }

/* ── Download button ── */
.stDownloadButton > button {
  background: transparent !important;
  color: var(--vert) !important;
  border: 2px solid var(--vert) !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
  background: white !important;
  border: 2px dashed var(--bordure) !important;
  border-radius: 10px !important;
  padding: 1rem !important;
}

/* ── Métriques ── */
[data-testid="metric-container"] {
  background: white;
  border: 1px solid var(--bordure);
  border-radius: 10px;
  padding: 1rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
  font-family: 'Syne', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.04em !important;
}

/* ── Section titres ── */
h2, h3 {
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
}

/* ── Alerte info ── */
.note-methodo {
  background: #EDF4F1;
  border: 1px solid var(--vert-clair);
  border-left: 4px solid var(--vert);
  border-radius: 8px;
  padding: 0.9rem 1.2rem;
  font-size: 0.87rem;
  font-style: italic;
  color: var(--vert);
  margin-bottom: 1.5rem;
}

/* ── Barre de progression thème ── */
.barre-theme { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.barre-theme .nom { font-family: 'Syne', sans-serif; font-size: 0.82rem; width: 110px; font-weight: 600; }
.barre-theme .piste { flex: 1; background: var(--creme); border-radius: 4px; height: 8px; overflow: hidden; }
.barre-theme .rempli { height: 8px; border-radius: 4px; }
.barre-theme .val { font-family: 'Syne', sans-serif; font-size: 0.8rem; color: var(--gris); width: 40px; text-align: right; }
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
            "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne",
            "Centre-Val-de-Loire", "Grand-Est", "Hauts-de-France",
            "Île-de-France", "Normandie", "Nouvelle-Aquitaine",
            "Occitanie", "Pays-de-la-Loire", "Provence-Alpes-Côte-d'Azur",
            "Autre / Non spécifiée",
        ],
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

        # Collecte des passages à afficher
        icons = {"avifaune": "🦅", "chiropteres": "🦇",
                 "zones_humides": "💧", "paysage": "🌄"}
        badge_css = {"avifaune": "badge-avifaune", "chiropteres": "badge-chiro",
                     "zones_humides": "badge-humides", "paysage": "badge-paysage"}
        border_css = {"avifaune": "carte-avifaune", "chiropteres": "carte-chiro",
                      "zones_humides": "carte-humides", "paysage": "carte-paysage"}

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
            date_str = f"{doc.get('month','?')}/{doc.get('year','?')}" if doc.get('year') else "date inconnue"
            st.markdown(f"#### 📄 {doc.get('text','')[:80]} — *{doc.get('region','')} · {date_str}*")

            for p in doc_passages[:10]:  # Limiter à 10 passages par doc pour la lisibilité
                dom = p.get("dominant_theme", "")
                themes_badges = " ".join(
                    f'<span class="badge {badge_css.get(th,"")}">{icons.get(th,"")} {THEMES_FR.get(th,th)}</span>'
                    for th in p.get("themes", {})
                )
                art = f'<span class="article-tag">{p["article_ref"]}</span>' if p.get("article_ref") else ""
                score = p.get("themes", {}).get(dom, 0)
                text_esc = (p.get("text","") or "").replace("<","&lt;").replace(">","&gt;")
                text_esc = text_esc[:500] + ("…" if len(text_esc) > 500 else "")

                st.markdown(f"""
                <div class="extrait-card {border_css.get(dom,'') }">
                  <div class="meta">
                    {art} {themes_badges}
                    <span class="score-pill">Score {score}</span>
                  </div>
                  <blockquote>{text_esc}</blockquote>
                </div>
                """, unsafe_allow_html=True)
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
