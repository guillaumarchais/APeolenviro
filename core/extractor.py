"""
core/extractor.py
=================
Extraction de texte et classification thématique des arrêtés préfectoraux éoliens.

Ce module gère trois niveaux d'extraction, appliqués automatiquement dans l'ordre :
  1. pdfplumber   — PDFs nativement numériques (le cas le plus fréquent)
  2. pypdf        — fallback pour les encodages non standards (documents anciens)
  3. Tesseract    — OCR pour les PDFs scannés (images), avec téléchargement
                   automatique du modèle français fra.traineddata si absent

Corrections clés par rapport aux versions précédentes :
  - Correctif du curseur BytesIO (bug Streamlit UploadedFile)
  - Heuristique de détection scan basée sur le total de caractères alpha (>= 200)
  - Téléchargement automatique de fra.traineddata via apt puis GitHub
"""

# ── Imports standard ──────────────────────────────────────────────────────────
import io
import os
import re
import shutil
import subprocess
import urllib.request
from typing import Optional

# ── Import tiers ──────────────────────────────────────────────────────────────
import pdfplumber


# =============================================================================
# SECTION 1 — Thèmes et mots-clés
# =============================================================================

THEMES_FR = {
    "avifaune":      "Avifaune",
    "chiropteres":   "Chiroptères",
    "zones_humides": "Zones humides",
    "paysage":       "Paysage",
}

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

# Seuil minimum de score pour qu'un passage soit attribué à un thème.
# Mots-clés forts = 2 pts, faibles = 1 pt par occurrence.
CLASSIFICATION_THRESHOLD = 2


def normalize(text: str) -> str:
    """Minuscules + suppression des accents pour la comparaison de mots-clés."""
    text = text.lower()
    for src, dst in {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "î": "i", "ï": "i",
        "ç": "c", "œ": "oe", "æ": "ae",
    }.items():
        text = text.replace(src, dst)
    return text


# Pré-normalisation des mots-clés : on ne le fait qu'une seule fois au chargement
# du module, pour éviter de répéter ce travail à chaque appel de classify_passage.
THEMES_NORM = {
    th: {
        "strong": [normalize(k) for k in kws["strong"]],
        "weak":   [normalize(k) for k in kws["weak"]],
    }
    for th, kws in THEMES.items()
}


# =============================================================================
# SECTION 2 — OCR : téléchargement automatique du modèle français Tesseract
# =============================================================================

# Emplacement système de tessdata (Linux standard, Debian/Ubuntu).
TESSDATA_SYSTEM = "/usr/share/tesseract-ocr/5/tessdata"

# Dossier de cache local : utilisé quand /usr/share/ est en lecture seule
# (cas de Streamlit Cloud Community et de certains environnements sandboxés).
TESSDATA_LOCAL = os.path.expanduser("~/.tessdata")

# URLs du fichier fra.traineddata sur le dépôt officiel Tesseract.
# On essaie d'abord "tessdata_best" (modèle LSTM haute précision, ~10 Mo),
# puis le dépôt standard (~5 Mo) comme secours si le premier est indisponible.
FRA_URL_BEST     = "https://github.com/tesseract-ocr/tessdata_best/raw/main/fra.traineddata"
FRA_URL_STANDARD = "https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata"


def _fra_traineddata_path() -> Optional[str]:
    """
    Recherche fra.traineddata dans les emplacements connus.
    Retourne le chemin complet si le fichier est trouvé, None sinon.
    L'ordre de priorité est : dossier système, puis cache local ~/.tessdata.
    """
    for folder in (TESSDATA_SYSTEM, TESSDATA_LOCAL):
        candidate = os.path.join(folder, "fra.traineddata")
        if os.path.exists(candidate):
            return candidate
    return None


def ensure_french_tesseract() -> tuple[bool, str]:
    """
    Garantit que le modèle français de Tesseract (fra.traineddata) est disponible
    sur le système avant de lancer l'OCR. Retourne (succès, message_diagnostic).

    La stratégie se déroule en trois étapes successives, de la plus simple
    à la plus autonome :

    Étape 1 — Vérification rapide
        Si fra.traineddata existe déjà (installé manuellement, via apt au démarrage
        de l'app avec packages.txt, ou issu d'un téléchargement précédent mis en
        cache dans ~/.tessdata), on retourne immédiatement sans rien faire.

    Étape 2 — Installation via apt-get
        On tente d'installer le paquet tesseract-ocr-fra via apt-get. Cette étape
        réussit sur Streamlit Cloud Community si on n'a pas de packages.txt, et sur
        tout Linux avec les droits sudo. Elle est silencieusement ignorée si apt
        est indisponible (macOS, Windows, droits insuffisants).

    Étape 3 — Téléchargement direct depuis GitHub
        En dernier recours, on télécharge fra.traineddata directement depuis le
        dépôt officiel GitHub de Tesseract-OCR et on le place dans ~/.tessdata.
        On positionne ensuite la variable d'environnement TESSDATA_PREFIX pour que
        Tesseract sache où chercher. Le fichier est conservé entre les sessions
        (cache persistant), donc ce téléchargement ne se produit qu'une seule fois.
    """
    # ── Étape 1 : déjà présent ? ──────────────────────────────────────────────
    if _fra_traineddata_path():
        os.environ["TESSDATA_PREFIX"] = os.path.dirname(_fra_traineddata_path())
        return True, "fra.traineddata déjà disponible"

    # ── Étape 2 : tentative via apt-get ──────────────────────────────────────
    try:
        result = subprocess.run(
            ["apt-get", "install", "-y", "tesseract-ocr-fra"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and _fra_traineddata_path():
            os.environ["TESSDATA_PREFIX"] = os.path.dirname(_fra_traineddata_path())
            return True, "fra.traineddata installé via apt-get"
    except Exception:
        # apt absent (macOS, Windows) ou droits insuffisants → étape suivante
        pass

    # ── Étape 3 : téléchargement direct depuis GitHub ─────────────────────────
    os.makedirs(TESSDATA_LOCAL, exist_ok=True)
    dest       = os.path.join(TESSDATA_LOCAL, "fra.traineddata")
    last_error = "aucune URL tentée"

    for url in (FRA_URL_BEST, FRA_URL_STANDARD):
        try:
            req = urllib.request.Request(
                url,
                # GitHub requiert un User-Agent non vide pour servir les fichiers raw
                headers={"User-Agent": "Mozilla/5.0 (compatible; DREAL-Extractor/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=90) as response, \
                 open(dest, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

            # Un fra.traineddata valide fait toujours plus de 1 Mo.
            # Un fichier plus petit indique un téléchargement partiel ou une réponse HTML d'erreur.
            size_kb = os.path.getsize(dest) // 1024
            if size_kb > 1000:
                os.environ["TESSDATA_PREFIX"] = TESSDATA_LOCAL
                return True, f"fra.traineddata téléchargé ({size_kb} Ko) depuis {url}"
            else:
                os.remove(dest)
                last_error = f"Fichier trop petit ({size_kb} Ko) depuis {url}"

        except Exception as e:
            last_error = f"{url} → {e}"
            # On passe à l'URL de secours
            continue

    return False, f"Impossible d'obtenir fra.traineddata : {last_error}"


def _tesseract_lang() -> str:
    """
    Retourne la langue Tesseract à utiliser.
    Retourne 'fra' si le modèle français est disponible, 'eng' sinon.
    Le modèle anglais produit des résultats acceptables sur du français
    pour les mots courants, mais fait des erreurs sur les accents et
    certains caractères spéciaux (é, è, ç, œ...).
    """
    path = _fra_traineddata_path()
    if path:
        os.environ["TESSDATA_PREFIX"] = os.path.dirname(path)
        return "fra"
    return "eng"


def extract_text_with_ocr(pdf_bytes: bytes) -> tuple[str, str]:
    """
    Applique l'OCR Tesseract sur un PDF scanné.
    Retourne (texte_extrait, message_diagnostic).

    Le pipeline OCR fonctionne en trois temps :
      1. ensure_french_tesseract() télécharge le modèle français si nécessaire
      2. pdf2image convertit chaque page PDF en image PIL à 300 dpi
         (résolution minimale recommandée pour un OCR de qualité sur des
         documents administratifs avec des caractères de taille normale)
      3. pytesseract applique Tesseract avec --psm 1 (détection automatique
         de la mise en page) et --oem 1 (moteur LSTM, plus précis que le moteur
         basé sur les patterns)
    """
    # Télécharger le modèle français si absent (positionne aussi TESSDATA_PREFIX)
    ok_dl, msg_dl = ensure_french_tesseract()

    # Vérifier les dépendances OCR
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError as e:
        return "", (
            f"Dépendance OCR manquante : {e}. "
            "Ajoutez pdf2image et pytesseract à requirements.txt."
        )

    # Convertir les pages PDF en images PIL
    try:
        images = convert_from_bytes(pdf_bytes, dpi=300)
    except Exception as e:
        return "", f"Conversion PDF -> image échouée : {e}"

    lang = _tesseract_lang()

    # --psm 1 : détection automatique de l'orientation de la page et du type de mise en page
    # --oem 1 : utiliser uniquement le moteur LSTM (réseau de neurones), plus précis
    tess_config = "--psm 1 --oem 1"

    pages_text = []
    errors     = []

    for i, img in enumerate(images, 1):
        try:
            text = pytesseract.image_to_string(img, lang=lang, config=tess_config)
            pages_text.append(text)
        except Exception as e:
            errors.append(f"p.{i}: {e}")
            # On insère une chaîne vide pour conserver la numérotation des pages
            pages_text.append("")

    full_text  = "\n\x0c\n".join(pages_text)  # \x0c = saut de page standard PDF
    alpha      = sum(1 for c in full_text if c.isalpha())
    error_info = f" | Erreurs sur {len(errors)} page(s)" if errors else ""
    diag       = (
        f"OCR Tesseract ({lang}) — {len(images)} pages, {alpha:,} caractères"
        f" | {msg_dl}{error_info}"
    )
    return full_text, diag


# =============================================================================
# SECTION 3 — Extraction de texte (pipeline principal)
# =============================================================================

def extract_text_from_bytes(pdf_bytes: bytes) -> tuple[str, bool, str]:
    """
    Extrait le texte d'un PDF fourni en bytes (issu d'un st.file_uploader Streamlit).
    Retourne (texte_brut, succès, message_diagnostic).

    Le pipeline essaie trois méthodes dans l'ordre, et s'arrête dès qu'une
    d'entre elles produit assez de texte (>= 200 caractères alphabétiques) :

      1. pdfplumber  : idéal pour les PDFs nativement numériques
      2. pypdf       : meilleure gestion de certains encodages non standards
      3. OCR         : pour les PDFs scannés (images), avec téléchargement
                       automatique du modèle français Tesseract

    Correctif du curseur BytesIO (bug Streamlit)
    --------------------------------------------
    L'objet UploadedFile retourné par st.file_uploader() possède un curseur
    interne de lecture. Si quelque chose a déjà appelé .read() sur cet objet
    (ce que Streamlit peut faire en interne), le curseur est en fin de flux et
    tout appel suivant à .read() retourne 0 bytes.
    Solution : appeler f.seek(0) PUIS f.read() une seule fois dans app.py,
    stocker les bytes dans une variable locale, et passer cette variable à ce
    module. Ici, on appelle toujours buf.seek(0) avant d'ouvrir le BytesIO
    avec pdfplumber ou pypdf, par mesure de défense supplémentaire.
    """

    # ── Tentative 1 : pdfplumber ─────────────────────────────────────────────
    diag_pdfplumber = "pdfplumber non tenté"
    combined        = ""
    try:
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)  # défense contre le bug curseur Streamlit

        pages_text = []
        n_pages    = 0
        with pdfplumber.open(buf) as pdf:
            n_pages = len(pdf.pages)
            for page in pdf.pages:
                # layout=False est plus robuste sur les arrêtés avec tableaux
                t = page.extract_text(layout=False)
                if t and t.strip():
                    pages_text.append(t)

        combined    = "\n\x0c\n".join(pages_text)
        alpha_count = sum(1 for c in combined if c.isalpha())

        if alpha_count >= 200:
            return combined, True, f"pdfplumber OK — {n_pages} pages, {alpha_count:,} caractères"

        diag_pdfplumber = (
            f"pdfplumber : {alpha_count} caractères alpha sur {n_pages} pages (insuffisant)"
        )

    except Exception as e:
        diag_pdfplumber = f"pdfplumber exception : {e}"
        combined        = ""

    # ── Tentative 2 : pypdf (fallback encodages non standards) ───────────────
    # Certains PDFs administratifs produits par de vieux logiciels bureautiques
    # utilisent des encodages de polices que pdfplumber ne décode pas correctement.
    # pypdf gère mieux ces cas.
    diag_pypdf  = "pypdf non tenté"
    combined_fb = ""
    try:
        import pypdf
        buf2 = io.BytesIO(pdf_bytes)
        buf2.seek(0)

        reader        = pypdf.PdfReader(buf2)
        pages_text_fb = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                pages_text_fb.append(t)

        combined_fb = "\n\x0c\n".join(pages_text_fb)
        alpha_fb    = sum(1 for c in combined_fb if c.isalpha())

        if alpha_fb >= 200:
            return combined_fb, True, f"pypdf fallback OK — {alpha_fb:,} caractères"

        diag_pypdf = f"pypdf : {alpha_fb} caractères alpha (insuffisant)"

    except ImportError:
        diag_pypdf = "pypdf non installé"
    except Exception as e:
        diag_pypdf = f"pypdf exception : {e}"

    # ── Tentative 3 : OCR Tesseract ──────────────────────────────────────────
    # Les deux extracteurs de texte natif ont échoué : le PDF est très
    # probablement un scan (image). On bascule sur l'OCR automatiquement.
    # ensure_french_tesseract() est appelé à l'intérieur et télécharge
    # fra.traineddata si nécessaire (une seule fois, puis mis en cache local).
    ocr_text, ocr_diag = extract_text_with_ocr(pdf_bytes)
    alpha_ocr = sum(1 for c in ocr_text if c.isalpha())

    if alpha_ocr >= 200:
        return ocr_text, True, f"OCR automatique (scan détecté). {ocr_diag}"

    # Aucune méthode n'a produit de texte utilisable
    return "", False, (
        f"Échec complet. {diag_pdfplumber} | {diag_pypdf} | "
        f"OCR : {alpha_ocr} chars ({ocr_diag})"
    )


# =============================================================================
# SECTION 4 — Segmentation du texte en passages logiques
# =============================================================================

def split_into_passages(
    raw_text: str,
) -> list[tuple[str, int, Optional[str]]]:
    """
    Découpe le texte brut en passages logiques pour la classification.
    Retourne une liste de (texte_du_passage, n°page_approx, ref_article).

    On cherche d'abord les marqueurs d'articles réglementaires
    ("Article II.1.a", "Art. 4", "ARTICLE 3"...), car les arrêtés préfectoraux
    sont structurés en articles. Chaque article devient un passage.
    Si aucun article n'est détecté sur une page, on découpe par paragraphes
    (séparés par des lignes vides), ce qui couvre les considérants et pages de garde.
    """
    pages       = raw_text.split("\x0c")
    article_pat = re.compile(
        r"(Article\s+[\w\.\-]+|Art\.\s*[\w\.\-]+|ARTICLE\s+[\w\.\-]+)",
        re.IGNORECASE,
    )
    passages = []

    for page_num, page_text in enumerate(pages, 1):
        parts = article_pat.split(page_text)

        if len(parts) > 1:
            # La page contient des marqueurs d'articles : on itère par paires
            # (ref_article, contenu_article)
            i = 1
            while i < len(parts) - 1:
                ref     = parts[i].strip()
                content = parts[i + 1].strip()
                if len(content) > 80:
                    passages.append((content, page_num, ref))
                i += 2
        else:
            # Pas d'articles détectés : découpage par paragraphes
            for para in re.split(r"\n{2,}", page_text):
                para = para.strip()
                if len(para) > 120:
                    passages.append((para, page_num, None))

    return passages


# =============================================================================
# SECTION 5 — Classification thématique
# =============================================================================

def classify_passage(
    text: str,
    active_themes: Optional[list] = None,
) -> dict:
    """
    Calcule un score de pertinence par thématique pour un passage de texte.
    Retourne un dict {theme: score} pour les thèmes dépassant le seuil.

    Chaque occurrence d'un mot-clé fort vaut 2 points, chaque occurrence d'un
    mot-clé faible vaut 1 point. Un même mot-clé peut contribuer plusieurs fois
    s'il apparaît plusieurs fois dans le passage. Seuls les thèmes listés dans
    active_themes sont évalués (tous par défaut).
    """
    if active_themes is None:
        active_themes = list(THEMES_NORM.keys())

    text_n = normalize(text)
    scores = {}

    for th, kws in THEMES_NORM.items():
        if th not in active_themes:
            continue
        score  = sum(text_n.count(k) * 2 for k in kws["strong"])
        score += sum(text_n.count(k) * 1 for k in kws["weak"])
        if score >= CLASSIFICATION_THRESHOLD:
            scores[th] = score

    return scores


# =============================================================================
# SECTION 6 — Pipeline principal (bytes -> dict de résultats)
# =============================================================================

def parse_arrete_from_bytes(
    pdf_bytes: bytes,
    metadata: dict,
    active_themes: Optional[list] = None,
) -> dict:
    """
    Point d'entrée principal pour l'application Streamlit.
    Prend les bytes d'un PDF uploadé et les métadonnées saisies par l'utilisateur,
    retourne un dict complet avec les passages classifiés et les métadonnées enrichies.

    En cas d'échec d'extraction, retourne quand même un dict cohérent avec
    extraction_ok=False et un message d'erreur explicite affiché dans l'UI.
    """
    if active_themes is None:
        active_themes = list(THEMES_FR.keys())

    # Extraction du texte : pdfplumber -> pypdf -> OCR automatique si scan
    raw_text, ok, diag = extract_text_from_bytes(pdf_bytes)

    if not ok or not raw_text.strip():
        return {
            **metadata,
            "extraction_ok": False,
            "error_msg": diag,
            "themes_found": [],
            "total_passages_with_themes": 0,
            "passages": [],
        }

    # Segmentation du texte en passages logiques (par articles puis paragraphes)
    raw_passages = split_into_passages(raw_text)

    # Classification thématique de chaque passage
    passages = []
    for (text, page_num, article_ref) in raw_passages:
        themes = classify_passage(text, active_themes)
        if themes:
            dominant = max(themes, key=themes.get)
            passages.append({
                "text":           text[:1000],  # tronqué pour limiter la taille des résultats
                "page_num":       page_num,
                "article_ref":    article_ref,
                "themes":         themes,
                "dominant_theme": dominant,
            })

    return {
        **metadata,
        "extraction_ok":              True,
        "error_msg":                  diag,
        "themes_found":               list({th for p in passages for th in p["themes"]}),
        "total_passages_with_themes": len(passages),
        "passages":                   passages,
    }


# =============================================================================
# SECTION 7 — Utilitaires
# =============================================================================

def extract_date_from_filename(filename: str) -> dict:
    """
    Tente d'extraire l'année et le mois depuis le nom d'un fichier PDF.
    Retourne {"year": "2023", "month": "07"} ou {"year": None, "month": None}.

    Formats numériques reconnus : 2023-07, 2023_07, 07-2023, 20230715.
    Noms de mois en français également reconnus : "janvier2023", "mars 2024", etc.
    """
    mois_fr = {
        "janvier":   "01", "fevrier":  "02", "mars":     "03", "avril":    "04",
        "mai":       "05", "juin":     "06", "juillet":  "07", "aout":     "08",
        "septembre": "09", "octobre":  "10", "novembre": "11", "decembre": "12",
    }
    # Patterns numériques : (regex, groupe_année, groupe_mois)
    patterns = [
        (r"(\d{4})[_\-](\d{2})", 1, 2),   # 2023-07 ou 2023_07
        (r"(\d{2})[_\-](\d{4})", 2, 1),   # 07-2023
        (r"(\d{4})(\d{2})\d{2}", 1, 2),   # 20230715
    ]
    for pat, yi, mi in patterns:
        m = re.search(pat, filename)
        if m:
            return {"year": m.group(yi), "month": m.group(mi).zfill(2)}

    # Noms de mois en français (après normalisation des accents)
    fn_norm = normalize(filename)
    for mois, num in mois_fr.items():
        m = re.search(mois + r"\s*(20\d{2})", fn_norm)
        if m:
            return {"year": m.group(1), "month": num}

    return {"year": None, "month": None}
