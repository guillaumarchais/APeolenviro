"""
core/extractor.py
=================
Version adaptée pour Streamlit : prend des bytes PDF en entrée
plutôt qu'un chemin de fichier, ce qui permet de traiter les
fichiers uploadés directement en mémoire sans les écrire sur disque.
"""

import pdfplumber
import re
import io
from typing import Optional
from dataclasses import dataclass, field

# ─── Thèmes et libellés français ─────────────────────────────────────────────

THEMES_FR = {
    "avifaune":     "Avifaune",
    "chiropteres":  "Chiroptères",
    "zones_humides": "Zones humides",
    "paysage":      "Paysage",
}

# ─── Mots-clés par thématique ────────────────────────────────────────────────

THEMES = {
    "avifaune": {
        "strong": [
            "avifaune", "avifaunistique", "oiseaux", "rapaces", "rapace",
            "milan royal", "milan noir", "busard", "outarde", "cigogne",
            "grue cendrée", "aigle", "faucon", "buse", "héron",
            "espèces nicheuses", "espèces migratoires", "couloir migratoire",
            "migration", "nidification", "effarouchement", "bridage avifaune",
            "suivi ornithologique", "ornithologique", "ornithologie",
            "liste rouge oiseaux", "directive oiseaux",
            "zone de protection spéciale", "ZPS",
            "mortalité avifaune", "collision oiseaux",
        ],
        "weak": [
            "faune", "espèces protégées", "habitat", "natura 2000",
            "sensibilité faunistique", "suivi faune", "bilan ornithologique",
            "impacts sur la faune", "mesures de réduction faune",
        ],
    },
    "chiropteres": {
        "strong": [
            "chiroptère", "chiroptères", "chauve-souris", "chauves-souris",
            "pipistrelle", "noctule", "sérotine", "murin", "grand murin",
            "rhinolophe", "vespertilion", "barbastelle", "oreillard",
            "minioptère", "tadaride",
            "activité chiroptérologique", "chiroptérologique",
            "gîte", "hibernation", "transit", "chasse chiroptères",
            "bridage chiroptères", "bridage acoustique",
            "détection ultrasonique", "détecteur ultrasons",
            "mortalité chiroptères", "directive habitats faune flore",
        ],
        "weak": [
            "faune", "espèces protégées", "habitat", "natura 2000",
            "espèces nocturnes", "suivi faune",
            "impacts sur la faune", "mesures de réduction faune",
        ],
    },
    "zones_humides": {
        "strong": [
            "zone humide", "zones humides", "zone humide avérée",
            "délimitation zone humide", "inventaire zone humide",
            "diagnostic pédologique", "diagnostic floristique zone humide",
            "habitat humide", "prairie humide", "tourbière", "marais",
            "roselière", "jonçaie", "mégaphorbiaie", "mare",
            "loi sur l'eau", "IOTA", "dossier loi sur l'eau",
            "arrêté loi sur l'eau", "autorisation loi sur l'eau",
            "coefficient d'humidité", "hydromorphie",
            "compensation zones humides", "recréation zone humide",
            "SDAGE", "SAGE", "masse d'eau",
        ],
        "weak": [
            "milieu aquatique", "biodiversité", "flore", "végétation",
            "espèces hygrophiles", "milieux humides",
            "impacts sur les milieux", "mesures compensatoires",
        ],
    },
    "paysage": {
        "strong": [
            "paysage", "paysager", "paysagère", "insertion paysagère",
            "intégration paysagère", "impact paysager", "impact visuel",
            "covisibilité", "co-visibilité", "intervisibilité",
            "aire d'étude paysagère", "photomontage", "simulation visuelle",
            "monument historique", "site classé", "site inscrit",
            "ZPPAUP", "AVAP", "site patrimonial remarquable",
            "ABF", "architecte des bâtiments de france",
            "éloignement visuel", "point de vue", "perception visuelle",
            "mesures paysagères", "haie bocagère", "traitement visuel",
            "balisage diurne", "balisage nocturne",
            "couleur des éoliennes", "ombre portée",
        ],
        "weak": [
            "patrimoine", "tourisme", "cadre de vie", "riverains",
            "aménagement du territoire", "urbanisme",
            "plan local d'urbanisme", "PLU", "SCoT",
            "charte paysagère",
        ],
    },
}

CLASSIFICATION_THRESHOLD = 2


def normalize(text: str) -> str:
    """Minuscules + suppression des accents pour la comparaison."""
    text = text.lower()
    for src, dst in {"é":"e","è":"e","ê":"e","ë":"e","à":"a","â":"a",
                     "ô":"o","ù":"u","û":"u","î":"i","ï":"i",
                     "ç":"c","œ":"oe","æ":"ae"}.items():
        text = text.replace(src, dst)
    return text


# Pré-normalisation pour éviter de refaire le travail à chaque appel
THEMES_NORM = {
    th: {
        "strong": [normalize(k) for k in kws["strong"]],
        "weak":   [normalize(k) for k in kws["weak"]],
    }
    for th, kws in THEMES.items()
}


# ─── Extraction de texte depuis bytes ────────────────────────────────────────

def extract_text_from_bytes(pdf_bytes: bytes) -> tuple[str, bool]:
    """
    Extrait le texte d'un PDF fourni en bytes (issu d'un st.file_uploader).
    Retourne (texte_brut, succès).
    Le booléen succès est False si le PDF semble être un scan.
    """
    try:
        buf = io.BytesIO(pdf_bytes)
        pages_text = []
        with pdfplumber.open(buf) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)

        combined = "\n".join(pages_text)
        # Heuristique : < 100 caractères par page → probablement scanné
        avg = len(combined) / max(1, len(pages_text))
        return combined, avg >= 100

    except Exception as e:
        return "", False


# ─── Segmentation en passages logiques ────────────────────────────────────────

def split_into_passages(raw_text: str) -> list[tuple[str, int, Optional[str]]]:
    """
    Découpe le texte en passages articulés autour des numéros d'articles.
    Retourne une liste de (texte, n°page_approx, ref_article).
    """
    pages = raw_text.split("\x0c")
    article_pat = re.compile(
        r"(Article\s+\d+[\.\-\d]*|Art\.\s*\d+[\.\-\d]*|ARTICLE\s+\d+[\.\-\d]*)",
        re.IGNORECASE
    )
    passages = []

    for page_num, page_text in enumerate(pages, 1):
        parts = article_pat.split(page_text)
        if len(parts) > 1:
            i = 1
            while i < len(parts) - 1:
                ref = parts[i].strip()
                content = parts[i + 1].strip()
                if len(content) > 80:
                    passages.append((content, page_num, ref))
                i += 2
        else:
            for para in re.split(r"\n{2,}", page_text):
                para = para.strip()
                if len(para) > 120:
                    passages.append((para, page_num, None))

    return passages


# ─── Classification thématique ────────────────────────────────────────────────

def classify_passage(text: str, active_themes: list = None) -> dict:
    """
    Calcule un score par thématique pour un passage.
    Ne traite que les thèmes listés dans active_themes (tous par défaut).
    """
    if active_themes is None:
        active_themes = list(THEMES_NORM.keys())
    text_n = normalize(text)
    scores = {}
    for th, kws in THEMES_NORM.items():
        if th not in active_themes:
            continue
        score = sum(text_n.count(k) * 2 for k in kws["strong"])
        score += sum(text_n.count(k) * 1 for k in kws["weak"])
        if score >= CLASSIFICATION_THRESHOLD:
            scores[th] = score
    return scores


# ─── Pipeline principal (bytes → résultat dict) ───────────────────────────────

def parse_arrete_from_bytes(pdf_bytes: bytes, metadata: dict,
                            active_themes: list = None) -> dict:
    """
    Point d'entrée principal pour Streamlit.
    Prend les bytes d'un PDF et les métadonnées, retourne un dict de résultats.
    """
    if active_themes is None:
        active_themes = list(THEMES_FR.keys())

    raw_text, ok = extract_text_from_bytes(pdf_bytes)

    if not ok or not raw_text.strip():
        return {
            **metadata,
            "extraction_ok": False,
            "error_msg": "PDF scanné ou texte non extractible (OCR nécessaire)",
            "themes_found": [],
            "total_passages_with_themes": 0,
            "passages": [],
        }

    raw_passages = split_into_passages(raw_text)
    passages = []

    for (text, page_num, article_ref) in raw_passages:
        themes = classify_passage(text, active_themes)
        if themes:
            dominant = max(themes, key=themes.get)
            passages.append({
                "text": text[:1000],
                "page_num": page_num,
                "article_ref": article_ref,
                "themes": themes,
                "dominant_theme": dominant,
            })

    return {
        **metadata,
        "extraction_ok": True,
        "error_msg": "",
        "themes_found": list({th for p in passages for th in p["themes"]}),
        "total_passages_with_themes": len(passages),
        "passages": passages,
    }


# ─── Utilitaire : extraction de date depuis un nom de fichier ────────────────

def extract_date_from_filename(filename: str) -> dict:
    """Tente d'extraire année et mois depuis un nom de fichier PDF."""
    mois_fr = {
        "janvier":"01","fevrier":"02","mars":"03","avril":"04",
        "mai":"05","juin":"06","juillet":"07","aout":"08",
        "septembre":"09","octobre":"10","novembre":"11","decembre":"12"
    }
    patterns = [
        (r"(\d{4})[_\-](\d{2})", 1, 2),   # 2023-03 ou 2023_03
        (r"(\d{2})[_\-](\d{4})", 2, 1),   # 03-2023
        (r"(\d{4})(\d{2})\d{2}", 1, 2),   # 20230315
    ]
    for pat, yi, mi in patterns:
        m = re.search(pat, filename)
        if m:
            return {"year": m.group(yi), "month": m.group(mi).zfill(2)}

    fn_n = normalize(filename)
    for mois, num in mois_fr.items():
        m = re.search(mois + r"\s*(20\d{2})", fn_n)
        if m:
            return {"year": m.group(1), "month": num}

    return {"year": None, "month": None}
