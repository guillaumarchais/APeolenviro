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

def extract_text_from_bytes(pdf_bytes: bytes) -> tuple[str, bool, str]:
    """
    Extrait le texte d'un PDF fourni en bytes (issu d'un st.file_uploader).
    Retourne (texte_brut, succès, message_diagnostic).

    Corrections clés par rapport à la version initiale :

    1. CURSEUR BytesIO : après tout appel .read() sur un UploadedFile Streamlit,
       le curseur interne est en fin de flux. On crée systématiquement un nouveau
       BytesIO depuis les bytes bruts ET on appelle seek(0) avant toute ouverture
       par pdfplumber, ce qui garantit que le flux est lu depuis le début.

    2. HEURISTIQUE DE DÉTECTION SCAN améliorée : l'ancienne version (< 100 chars
       en moyenne) rejetait des arrêtés courts ou comportant des pages de garde
       quasi-vides. On compte maintenant le nombre total de caractères alphabétiques
       sur l'ensemble du document — un seuil absolu de 200 caractères est plus
       fiable qu'une moyenne par page.

    3. FALLBACK pypdf : si pdfplumber échoue (PDF corrompu, encodage non standard),
       on tente une seconde extraction avec pypdf, qui gère mieux certains PDFs
       administratifs anciens générés par des logiciels bureautiques obsolètes.
    """

    # ── Tentative 1 : pdfplumber ─────────────────────────────────────────────
    try:
        # CORRECTIF CURSEUR : toujours recréer un BytesIO frais depuis les bytes
        # bruts, et appeler seek(0) explicitement — c'est la ligne qui corrige
        # le bug principal.
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)  # ← correctif essentiel : repositionner le curseur au début

        pages_text = []
        n_pages = 0
        with pdfplumber.open(buf) as pdf:
            n_pages = len(pdf.pages)
            for page in pdf.pages:
                # extract_text() avec layout=True donne de meilleurs résultats
                # sur les PDFs avec des colonnes ou des tableaux
                t = page.extract_text(layout=False)
                if t and t.strip():
                    pages_text.append(t)

        combined = "\n\x0c\n".join(pages_text)  # \x0c = saut de page pour split_into_passages

        # HEURISTIQUE AMÉLIORÉE : compter les caractères alphabétiques réels
        # (pas les espaces ni la ponctuation) sur tout le document.
        # Un PDF nativement numérique d'un arrêté a forcément plus de 200 lettres.
        alpha_count = sum(1 for c in combined if c.isalpha())

        if alpha_count >= 200:
            return combined, True, f"pdfplumber OK — {n_pages} pages, {alpha_count} caractères"

        # Texte trop pauvre : tenter le fallback avant de conclure à un scan
        diag_pdfplumber = f"pdfplumber : {alpha_count} caractères alpha sur {n_pages} pages (insuffisant)"

    except Exception as e:
        diag_pdfplumber = f"pdfplumber exception : {e}"
        combined = ""

    # ── Tentative 2 : fallback pypdf ─────────────────────────────────────────
    # pypdf gère mieux certains encodages non standard fréquents dans les
    # documents produits par des logiciels administratifs français (ex. acrobat
    # writer < 2010, certains PDF/A produits par ELISE ou Pastell).
    try:
        import pypdf
        buf2 = io.BytesIO(pdf_bytes)
        buf2.seek(0)  # ← même correctif curseur

        reader = pypdf.PdfReader(buf2)
        pages_text_fb = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                pages_text_fb.append(t)

        combined_fb = "\n\x0c\n".join(pages_text_fb)
        alpha_fb = sum(1 for c in combined_fb if c.isalpha())

        if alpha_fb >= 200:
            return combined_fb, True, f"pypdf fallback OK — {alpha_fb} caractères"

        # Les deux extracteurs ont échoué : PDF probablement scanné
        return combined_fb or combined, False, (
            f"PDF probablement scanné (OCR nécessaire). "
            f"{diag_pdfplumber} | pypdf : {alpha_fb} caractères alpha"
        )

    except ImportError:
        # pypdf non installé : retourner ce qu'on a avec pdfplumber
        return combined, False, f"PDF non extractible. {diag_pdfplumber} (pypdf non disponible)"

    except Exception as e:
        return combined, False, f"PDF non extractible. {diag_pdfplumber} | pypdf exception : {e}"


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

    raw_text, ok, diag = extract_text_from_bytes(pdf_bytes)

    if not ok or not raw_text.strip():
        return {
            **metadata,
            "extraction_ok": False,
            "error_msg": diag,  # message de diagnostic précis affiché dans l'UI
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
