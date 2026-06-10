# 🌬️ AP Éolien Enviro — Application Streamlit
## Analyse automatisée des thématiques environnementales dans les arrêtés préfectoraux

Application Streamlit déployée sur [apeolenviro.streamlit.app](https://apeolenviro.streamlit.app)

---

## Objectif

Extraire, classifier et restituer les prescriptions environnementales contenues dans les arrêtés préfectoraux d'autorisation de parcs éoliens terrestres (régime ICPE / autorisation environnementale).

Les thématiques couvertes sont l'avifaune, les chiroptères, les zones humides et le paysage. L'application traite aussi bien les PDFs nativement numériques que les documents scannés.

---

## Fonctionnalités

### Analyse des PDFs

- Dépôt de un ou plusieurs PDFs par glisser-déposer ou sélection
- Mode démonstration intégré avec un arrêté réel (parc Suroûet, Normandie)
- Détection automatique du type d'arrêté (autorisation, modification, prescriptions complémentaires, mise en demeure, abrogation, consignation)
- Extraction du texte en cascade selon la nature du document :
  1. **pymupdf4llm** — Markdown structuré avec OCR Tesseract intégré, prioritaire pour tous les types de PDF
  2. **pdfplumber** — extraction native pour les PDFs numériques
  3. **pypdf** — fallback pour les encodages non standard
  4. **Tesseract OCR direct** — dernier recours, avec téléchargement automatique du modèle français `fra.traineddata`
- Classification par mots-clés sur 151 termes (116 forts, 35 faibles) répartis sur 4 thèmes
- Segmentation par article (reconnaissance des structures `Article II.x.y`)

### Interface (4 onglets)

**📖 Extraits par thème** — cartes thématiques avec badge de type d'arrêté, aperçu 5 lignes, mots-clés en gras, bouton « Voir tout », bouton copier.

**📋 Tableau de synthèse** — tableau filtrable par région et par thème, avec colonne « Type d'arrêté », heatmap colorée par densité thématique.

**📥 Exports** — quatre formats téléchargeables :
- CSV (compatible Excel / LibreOffice)
- HTML (rapport interactif navigable)
- JSON (données brutes)
- **Word (.docx)** — rapport structuré par thème avec page de garde, tableau de synthèse, extraits encadrés par couleur thématique, pied de page numéroté

**📄 Texte complet** — affichage du texte intégral extrait pour chaque document, en mode rendu Markdown ou texte brut, avec téléchargement `.md` et bouton copier.

---

## Structure du projet

```
apeolenviro/
├── app.py                  # Application Streamlit (interface, onglets, CSS)
├── pipeline.py             # Orchestrateur batch (hors Streamlit)
├── demo_pipeline.py        # Données de démonstration
├── core/
│   ├── extractor.py        # Extraction, OCR, segmentation, classification, détection de type
│   ├── reporter.py         # Agrégation des résultats, tableau de synthèse, rapport HTML
│   └── word_export.py      # Génération du rapport Word (python-docx, pur Python)
├── scripts/
│   ├── 01_scraper.py       # Scraping des arrêtés depuis les portails DREAL
│   ├── 02_extractor.py     # Extraction batch (version ligne de commande)
│   └── 03_reporter.py      # Reporting batch
├── requirements.txt
└── packages.txt
```

---

## Installation

### Prérequis système

```
# packages.txt (Streamlit Cloud) ou apt-get en local
tesseract-ocr
tesseract-ocr-fra
poppler-utils
```

### Dépendances Python

```
# requirements.txt
streamlit>=1.35
pdfplumber>=0.11
pypdf>=4.0
pymupdf4llm>=0.0.17
pymupdf>=1.24.0
pdf2image>=1.17.0
pytesseract>=0.3.13
python-docx>=1.1.0
pandas>=2.0
```

### Lancement local

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Pipeline d'extraction

### Cascade d'extraction (`core/extractor.py`)

Pour chaque PDF, l'extraction tente les méthodes dans l'ordre suivant :

```
pymupdf4llm  →  pdfplumber  →  pypdf  →  Tesseract OCR direct
```

`pymupdf4llm` est prioritaire car il produit un Markdown structuré (titres, listes, paragraphes) reconnaissable par le segmenteur d'articles, tout en gérant nativement les PDFs scannés via Tesseract. Les PDFs 100 % scannés sont traités en ~60–90 secondes selon le nombre de pages.

Le Markdown brut est conservé dans la clé `raw_markdown` du résultat et affiché dans l'onglet **Texte complet**.

### Détection du type d'arrêté

Les 2 000 premiers caractères du texte extrait sont analysés par regex normalisées (insensibles aux accents) pour identifier parmi 6 types :

| Type | Exemples de marqueurs |
|---|---|
| Autorisation | `portant autorisation`, `est autorisée à exploiter` |
| Modification | `arrêté portant modification`, `modifiant l'arrêté` |
| Prescriptions complémentaires | `prescriptions complémentaires` |
| Mise en demeure | `mise en demeure` |
| Abrogation | `portant abrogation` |
| Consignation | `portant consignation` |

### Classification thématique

Chaque passage segmenté est scoré par somme pondérée des occurrences de mots-clés :

- **Mots forts** (présents dans l'article) : 2 points
- **Mots faibles** (partagés entre thèmes) : 1 point

Un passage est retenu s'il totalise un score ≥ 1 dans au moins un thème. Le `dominant_theme` est le thème au score le plus élevé.

| Thème | Mots-clés forts | Exemples |
|---|---|---|
| Avifaune | 30 | milan royal, suivi ornithologique, ZPS, migration |
| Chiroptères | 28 | bridage chiroptères, pipistrelle, gîte, détecteur ultrasons |
| Zones humides | 30 | zone humide avérée, diagnostic pédologique, SDAGE, ripisylve |
| Paysage | 28 | covisibilité, photomontage, ABF, étude paysagère |

---

## Export Word

Le rapport Word est généré en Python pur (`python-docx`, sans dépendance Node.js) via `core/word_export.py`. Il contient :

- **Page de garde** : titre, région, nombre de documents et d'extraits, date de génération
- **Tableau de synthèse** : passages, documents et score maximum par thème
- **Une section par thème** : extraits triés par score, groupés par document, dans des encadrés colorés avec bordure gauche thématique
- **Pied de page** numéroté (Page X / Y) sur toutes les pages

---

## Déploiement Streamlit Cloud

Le dépôt doit contenir à la racine :

- `requirements.txt` avec les dépendances Python
- `packages.txt` avec les paquets système (`tesseract-ocr`, `tesseract-ocr-fra`, `poppler-utils`)

Le modèle Tesseract français (`fra.traineddata`) est téléchargé automatiquement au premier lancement si `tesseract-ocr-fra` n'est pas disponible via `packages.txt`.

---

## Limitations connues

- Le temps d'extraction OCR (pymupdf4llm) est de l'ordre de 60–90 secondes pour un arrêté de 10–15 pages sur Streamlit Cloud.
- La classification par mots-clés ne capte pas les formulations atypiques ; un passage prescrivant le bridage sans utiliser le mot « chiroptère » sera manqué.
- Les tableaux et figures dans les PDFs scannés ne sont pas extraits.
- L'historique des analyses n'est pas persistant entre sessions (réinitialisation à la fermeture de l'onglet).
