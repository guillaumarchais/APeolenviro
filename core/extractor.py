"""
core/extractor.py
=================
Version adaptée pour Streamlit : prend des bytes PDF en entrée
plutôt qu'un chemin de fichier, ce qui permet de traiter les
fichiers uploadés directement en mémoire sans les écrire sur disque.

Corrections et améliorations :

  1. CURSEUR BytesIO : seek(0) systématique avant toute ouverture PDF.
  2. DÉTECTION SCAN améliorée : seuil de 200 caractères alphabétiques absolus.
  3. FALLBACK pypdf : si pdfplumber échoue sur un encodage non standard.
  4. OCR AUTOMATIQUE avec téléchargement du modèle français fra.traineddata.
"""

import io
import os
import re
import shutil
import subprocess
import urllib.request
from typing import Optional

import pdfplumber


# ══════════════════════════════════════════════════════════════════════════════
# THÈMES ET MOTS-CLÉS
# ══════════════════════════════════════════════════════════════════════════════

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
            "suivi avifaunistique", "bilan ornithologique",
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
            "nocturnes", "suivi", "mesures de réduction",
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
            "SDAGE", "masse d'eau", "pédologique"
        ],
        "weak": [
            "milieu aquatique", "flore", "végétation",
            "espèces hygrophiles", "milieux humides",
            "impacts sur les milieux",
        ],
    },
    "paysage": {
        "strong": [
            "paysage", "paysager", "paysagère", "insertion paysagère",
            "intégration paysagère", "impact paysager", "impact visuel",
            "covisibilité", "co-visibilité", "intervisibilité",
            "aire d'étude paysagère", "photomontage", "simulation visuelle",
            "monument historique", "site classé", "site inscrit", "site patrimonial remarquable",
            "ABF", "architecte des bâtiments de france",
            "éloignement visuel", "point de vue", "perception visuelle",
            "mesures paysagères", "haie bocagère", "traitement visuel",
            "balisage diurne", "balisage nocturne",
            "couleur des éoliennes", "ombre portée", "surplom", "saturation",
        ],
        "weak": [
            "patrimoine", "tourisme", "cadre de vie", "riverains",
            "plan local d'urbanisme", "PLU", "SCoT",
            "charte paysagère",
        ],
    },
}

CLASSIFICATION_THRESHOLD = 2


def normalize(text: str) -> str:
    """Minuscules + suppression des accents pour la comparaison par mots-clés."""
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


# Pré-normalisation une seule fois au chargement du module
THEMES_NORM = {
    th: {
        "strong": [normalize(k) for k in kws["strong"]],
        "weak":   [normalize(k) for k in kws["weak"]],
    }
    for th, kws in THEMES.items()
}


# ══════════════════════════════════════════════════════════════════════════════
# OCR — TÉLÉCHARGEMENT AUTOMATIQUE DU MODÈLE FRANÇAIS TESSERACT
# ══════════════════════════════════════════════════════════════════════════════

# Emplacement standard sur Ubuntu/Debian
TESSDATA_SYSTEM = "/usr/share/tesseract-ocr/5/tessdata"

# Cache local utilisé quand le dossier système est en lecture seule
# (cas typique sur Streamlit Cloud Community)
TESSDATA_LOCAL = os.path.expanduser("~/.tessdata")

# URLs officielles du modèle français Tesseract sur GitHub.
# On tente d'abord "tessdata_best" (précision maximale, ~4 Mo),
# puis "tessdata" standard (~2 Mo) en secours.
FRA_URL_BEST     = "https://github.com/tesseract-ocr/tessdata_best/raw/main/fra.traineddata"
FRA_URL_STANDARD = "https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata"


def _fra_traineddata_path() -> Optional[str]:
    """
    Cherche fra.traineddata dans le dossier système puis dans ~/.tessdata.
    Retourne le chemin complet si trouvé, None sinon.
    """
    for folder in (TESSDATA_SYSTEM, TESSDATA_LOCAL):
        path = os.path.join(folder, "fra.traineddata")
        if os.path.exists(path):
            return path
    return None


def _set_tessdata_prefix():
    """
    Positionne TESSDATA_PREFIX pour que Tesseract trouve ses modèles.
    Nécessaire uniquement quand le fichier est dans ~/.tessdata (dossier non standard).
    """
    local_path = os.path.join(TESSDATA_LOCAL, "fra.traineddata")
    if os.path.exists(local_path):
        os.environ["TESSDATA_PREFIX"] = TESSDATA_LOCAL


def ensure_french_tesseract() -> tuple[bool, str]:
    """
    Garantit que le modèle français Tesseract (fra.traineddata) est disponible.
    Retourne (succès: bool, message_diagnostic: str).

    La stratégie se déroule en trois étapes successives :

    Étape 1 — Vérification locale
        Si fra.traineddata est déjà présent (dossier système ou cache ~/.tessdata),
        on positionne TESSDATA_PREFIX et on s'arrête immédiatement. C'est le
        chemin pris à partir du deuxième lancement, car le fichier est mis en cache.

    Étape 2 — Installation via apt
        Sur les environnements Linux avec droits sudo (dont Streamlit Cloud si
        le fichier packages.txt contient 'tesseract-ocr-fra'), apt installe le
        paquet officiellement. On valide ensuite que le fichier est apparu.

    Étape 3 — Téléchargement direct depuis GitHub
        Si apt n'est pas disponible ou échoue, on télécharge fra.traineddata
        directement depuis le dépôt officiel Tesseract sur GitHub, on le place
        dans ~/.tessdata, et on positionne TESSDATA_PREFIX. On tente d'abord
        le modèle "best" (plus précis), puis le modèle standard en secours.
    """
    # ── Étape 1 : déjà présent ? ──────────────────────────────────────────────
    if _fra_traineddata_path():
        _set_tessdata_prefix()
        return True, "fra.traineddata déjà disponible"

    # ── Étape 2 : tentative apt ───────────────────────────────────────────────
    try:
        result = subprocess.run(
            ["apt-get", "install", "-y", "--no-install-recommends", "tesseract-ocr-fra"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and _fra_traineddata_path():
            _set_tessdata_prefix()
            return True, "fra.traineddata installé via apt"
    except Exception:
        pass  # apt absent ou timeout → on tente le téléchargement direct

    # ── Étape 3 : téléchargement direct depuis GitHub ─────────────────────────
    os.makedirs(TESSDATA_LOCAL, exist_ok=True)
    dest       = os.path.join(TESSDATA_LOCAL, "fra.traineddata")
    last_error = "aucune tentative effectuée"

    for url in (FRA_URL_BEST, FRA_URL_STANDARD):
        try:
            # GitHub requiert un User-Agent non vide pour les téléchargements directs
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as response, \
                 open(dest, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

            # Validation : un .traineddata valide fait toujours plus de 1 Mo
            size = os.path.getsize(dest)
            if size > 1_000_000:
                os.environ["TESSDATA_PREFIX"] = TESSDATA_LOCAL
                return True, (
                    f"fra.traineddata téléchargé depuis GitHub "
                    f"({size // 1024} Ko — {url.split('/')[2]})"
                )
            else:
                # Fichier trop petit = téléchargement partiel ou erreur HTTP silencieuse
                os.remove(dest)
                last_error = f"fichier trop petit ({size} octets) depuis {url}"

        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            if os.path.exists(dest):
                os.remove(dest)   # nettoyer le fichier partiel
            continue

    return False, (
        f"Impossible d'obtenir fra.traineddata — {last_error}. "
        "L'OCR utilisera le modèle anglais (eng) en secours."
    )


def _tesseract_lang() -> str:
    """
    Retourne 'fra' si le modèle français est disponible, 'eng' sinon.
    Le modèle anglais reste utilisable sur du français pour la classification
    par mots-clés normalisés (les accents sont de toute façon supprimés).
    """
    if _fra_traineddata_path():
        _set_tessdata_prefix()
        return "fra"
    return "eng"


def extract_text_with_ocr(pdf_bytes: bytes) -> tuple[str, str]:
    """
    Applique l'OCR Tesseract sur un PDF scanné fourni en bytes.
    Retourne (texte_extrait: str, message_diagnostic: str).

    Paramètres Tesseract utilisés :
      --psm 1 : détection automatique de l'orientation et de la mise en page
                (adapté aux documents multi-colonnes et aux tableaux)
      --oem 1 : moteur LSTM uniquement (plus précis que l'ancien moteur OCR 3)
      300 dpi : résolution minimale recommandée pour un OCR de qualité sur des
                documents administratifs avec de petites polices.
    """
    ok_dl, msg_dl = ensure_french_tesseract()

    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError as e:
        return "", (
            f"Dépendance OCR manquante : {e}. "
            "Ajoutez 'pdf2image' et 'pytesseract' dans requirements.txt."
        )

    try:
        images = convert_from_bytes(pdf_bytes, dpi=300)
    except Exception as e:
        return "", f"Conversion PDF→images échouée : {e}"

    lang       = _tesseract_lang()
    tess_cfg   = "--psm 1 --oem 1"
    pages_text = []
    errors     = []

    for i, img in enumerate(images, 1):
        try:
            text = pytesseract.image_to_string(img, lang=lang, config=tess_cfg)
            pages_text.append(text)
        except Exception as e:
            errors.append(f"p.{i}: {e}")
            pages_text.append("")   # page vide pour conserver la numérotation

    full_text  = "\n\x0c\n".join(pages_text)
    alpha      = sum(1 for c in full_text if c.isalpha())
    error_info = f" | Erreurs : {'; '.join(errors)}" if errors else ""
    diag = (
        f"OCR Tesseract ({lang}) — {len(images)} pages, {alpha:,} caractères"
        f" | {msg_dl}{error_info}"
    )
    return full_text, diag


# ══════════════════════════════════════════════════════════════════════════════
# EXTRACTION DE TEXTE DEPUIS BYTES
# ══════════════════════════════════════════════════════════════════════════════

def extract_text_from_bytes(pdf_bytes: bytes) -> tuple[str, bool, str]:
    """
    Tente d'extraire le texte d'un PDF en bytes. Enchaîne trois méthodes :
      1. pdfplumber  — extracteur principal (PDFs nativement numériques)
      2. pypdf       — fallback pour encodages non standard
      3. OCR Tesseract — fallback automatique pour les PDFs scannés

    Retourne (texte: str, succès: bool, diagnostic: str).

    Note sur le correctif curseur : on appelle systématiquement seek(0) avant
    chaque ouverture de BytesIO, car l'objet UploadedFile de Streamlit a un
    curseur interne qui peut déjà être en fin de flux après un premier read().
    """

    # ── Tentative 1 : pdfplumber ──────────────────────────────────────────────
    try:
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)   # ← correctif curseur

        pages_text = []
        n_pages    = 0
        with pdfplumber.open(buf) as pdf:
            n_pages = len(pdf.pages)
            for page in pdf.pages:
                t = page.extract_text(layout=False)
                if t and t.strip():
                    pages_text.append(t)

        combined    = "\n\x0c\n".join(pages_text)
        alpha_count = sum(1 for c in combined if c.isalpha())

        if alpha_count >= 200:
            return combined, True, f"pdfplumber OK — {n_pages} pages, {alpha_count:,} caractères"

        diag_pdfplumber = (
            f"pdfplumber : {alpha_count} chars alpha / {n_pages} pages (insuffisant)"
        )

    except Exception as e:
        diag_pdfplumber = f"pdfplumber exception : {e}"
        combined        = ""

    # ── Tentative 2 : pypdf ───────────────────────────────────────────────────
    try:
        import pypdf

        buf2 = io.BytesIO(pdf_bytes)
        buf2.seek(0)   # ← correctif curseur

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

        diag_pypdf = f"pypdf : {alpha_fb} chars alpha (insuffisant)"

    except ImportError:
        combined_fb = ""
        diag_pypdf  = "pypdf non installé"
    except Exception as e:
        combined_fb = ""
        diag_pypdf  = f"pypdf exception : {e}"

    # ── Tentative 3 : OCR Tesseract ───────────────────────────────────────────
    # Les deux extracteurs textuels ont échoué → PDF scanné détecté.
    # ensure_french_tesseract() télécharge le modèle français si nécessaire.
    ocr_text, ocr_diag = extract_text_with_ocr(pdf_bytes)
    alpha_ocr = sum(1 for c in ocr_text if c.isalpha())

    if alpha_ocr >= 200:
        return ocr_text, True, (
            f"PDF scanné → OCR automatique. "
            f"{diag_pdfplumber} | {diag_pypdf} | {ocr_diag}"
        )

    # Aucune méthode n'a produit de texte exploitable
    return "", False, (
        f"Échec complet. {diag_pdfplumber} | {diag_pypdf} | "
        f"OCR : {alpha_ocr} chars ({ocr_diag})"
    )


# ══════════════════════════════════════════════════════════════════════════════
# NETTOYAGE DU TEXTE OCR
# ══════════════════════════════════════════════════════════════════════════════

# Lignes parasites typiques produites par Tesseract sur les arrêtés préfectoraux :
# en-têtes ("Arrêté préfectoral — p 3/13"), pieds de page, numéros de page seuls,
# noms de préfecture seuls, tirets de séparation graphique.
_NOISE_PATTERNS = re.compile(
    r"^("
    r"\s*"                                          # ligne vide ou espaces
    r"|[-—=_]{3,}"                                  # séparateur graphique (---, ===…)
    r"|\d{1,3}"                                     # numéro de page seul (ex. "7")
    r"|\d{1,3}\s*/\s*\d{1,3}"                       # pagination (ex. "3/13", "p. 3/13")
    r"|p\.\s*\d{1,3}"                               # "p. 7"
    r"|Arrêté\s+préfectoral\s*[–—-].*"              # pied de page type DREAL
    r"|(?:Préfecture|PRÉFECTURE)\s+(?:de\s+(?:la\s+|du\s+|des\s+|l')?|d')[A-Z\w\s-]{2,40}$"
    r"|(?:Direction\s+régionale|DREAL|DRIEAT)\s+.*" # en-tête DREAL
    r")\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Coupure de mot en fin de ligne avec tiret (ex. "environ-\nnement")
_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")

# Saut de ligne SIMPLE au milieu d'une phrase : on le remplace par un espace.
# On ne touche PAS aux doubles sauts de ligne (vrais séparateurs de paragraphes)
# ni aux sauts de ligne qui suivent une ponctuation forte (. ; : !) car ils
# indiquent probablement une vraie fin de phrase ou de liste.
_SOFT_NEWLINE = re.compile(
    r"(?<![.;:!?\d])\n"   # saut de ligne non précédé d'une ponctuation forte
    r"(?!\n)"             # pas suivi d'un autre saut de ligne (garder les \n\n)
    r"(?![•\-–—\*])"      # pas suivi d'une puce de liste
    r"(?![A-Z]{2})"       # pas suivi d'un mot tout en majuscules (début de titre)
    r"(?!Article\s)"      # pas suivi d'un marqueur d'article
)

# Espaces multiples consécutifs (artéfact fréquent après correction des sauts de ligne)
_MULTI_SPACE = re.compile(r" {2,}")


def clean_ocr_text(text: str) -> str:
    """
    Nettoie le texte brut produit par Tesseract avant la segmentation en passages.

    Quatre opérations dans l'ordre :

    1. Suppression des lignes parasites — en-têtes, pieds de page, numéros de page,
       noms de préfecture ou de DREAL isolés sur une ligne. Ces éléments sont répétés
       sur chaque page du scan et pollueraient chaque passage classifié.

    2. Réparation des coupures de mots — Tesseract conserve les tirets de fin de ligne
       du document original ("environ-\\nement" → "environnement").

    3. Fusion des sauts de ligne mous — un saut de ligne simple au milieu d'une phrase
       est remplacé par un espace. On préserve les vrais séparateurs (double \\n,
       lignes commençant par une puce ou un titre en majuscules).

    4. Normalisation des espaces multiples — artéfact résiduel après l'étape 3.

    Le résultat est un texte où les paragraphes sont bien séparés par \\n\\n
    et les phrases ne sont plus découpées artificiellement, ce qui améliore
    significativement la précision de la classification thématique.
    """
    # 1. Supprimer les lignes parasites
    text = _NOISE_PATTERNS.sub("", text)

    # 2. Réparer les coupures de mots avec tiret
    text = _HYPHEN_BREAK.sub(r"\1\2", text)

    # 3. Fusionner les sauts de ligne mous en espace
    text = _SOFT_NEWLINE.sub(" ", text)

    # 4. Normaliser les espaces multiples
    text = _MULTI_SPACE.sub(" ", text)

    # 5. Réduire les suites de lignes vides (> 2) à exactement 2 sauts de ligne
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ══════════════════════════════════════════════════════════════════════════════
# SEGMENTATION EN PASSAGES LOGIQUES
# ══════════════════════════════════════════════════════════════════════════════

def split_into_passages(
    raw_text: str,
    is_ocr: bool = False,
) -> list[tuple[str, int, Optional[str]]]:
    """
    Découpe le texte brut en passages logiques.
    Retourne une liste de (texte_du_passage, numéro_de_page, ref_article).

    Si is_ocr=True, applique clean_ocr_text() sur chaque page avant le découpage
    pour éliminer les artefacts Tesseract qui fragmentent les passages.

    On cherche d'abord les marqueurs d'articles réglementaires
    ("Article II.2.a", "Art. 4", "ARTICLE 3"…), qui correspondent à la
    structure canonique des arrêtés préfectoraux. Sur les pages sans article
    détecté (pages de garde, préambules), on découpe sur les doubles sauts de
    ligne et on ignore les blocs trop courts.

    Seuils de longueur minimale :
      - Passage issu d'un article : 60 caractères (les articles courts existent)
      - Passage issu d'un paragraphe : 100 caractères (évite les titres seuls)
    Ces seuils sont réduits pour le texte OCR car le nettoyage a déjà éliminé
    la plupart des lignes parasites.
    """
    pages = raw_text.split("\x0c")

    # Pattern élargi pour les formats d'articles rencontrés dans les arrêtés :
    # Article II.2.a  /  Article I.1  /  Art. 4  /  ARTICLE 3  /  Article II.1.b.
    article_pat = re.compile(
        r"(Article\s+[IVXivx\d][\w\.\-]*|Art\.\s*\d+[\.\-\d]*|ARTICLE\s+[IVX\d][\w\.\-]*)",
        re.IGNORECASE,
    )

    # Seuils adaptatifs : plus permissifs pour l'OCR car le texte est déjà nettoyé
    min_article_len = 50  if is_ocr else 80
    min_para_len    = 80  if is_ocr else 120

    passages = []

    for page_num, page_text in enumerate(pages, 1):
        # Nettoyage OCR appliqué page par page pour préserver les \x0c
        if is_ocr:
            page_text = clean_ocr_text(page_text)

        if not page_text.strip():
            continue

        parts = article_pat.split(page_text)

        if len(parts) > 1:
            i = 1
            while i < len(parts) - 1:
                ref     = parts[i].strip()
                content = parts[i + 1].strip()
                if len(content) > min_article_len:
                    passages.append((content, page_num, ref))
                i += 2
            # Texte avant le premier article (souvent titre du Titre)
            prefix = parts[0].strip()
            if len(prefix) > min_para_len:
                passages.append((prefix, page_num, None))
        else:
            for para in re.split(r"\n{2,}", page_text):
                para = para.strip()
                if len(para) > min_para_len:
                    passages.append((para, page_num, None))

    return passages


# ══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION THÉMATIQUE
# ══════════════════════════════════════════════════════════════════════════════

def classify_passage(text: str, active_themes: list = None) -> dict:
    """
    Calcule un score de pertinence par thématique pour un passage de texte.
    Retourne {theme_key: score} pour les thèmes dépassant CLASSIFICATION_THRESHOLD.

    Scoring : mot-clé fort = +2 par occurrence, mot-clé faible = +1 par occurrence.
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


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL  (bytes → dict de résultats)
# ══════════════════════════════════════════════════════════════════════════════

def parse_arrete_from_bytes(
    pdf_bytes: bytes,
    metadata: dict,
    active_themes: list = None,
) -> dict:
    """
    Point d'entrée principal pour Streamlit.
    Orchestre extraction, segmentation et classification pour un arrêté.

    Paramètres :
      pdf_bytes     — contenu brut du PDF (issu de UploadedFile.read())
      metadata      — dict avec : region, year, month, text, url, filename
      active_themes — thèmes à analyser (tous par défaut)

    Retourne un dict avec : extraction_ok, error_msg, themes_found,
    total_passages_with_themes, passages.
    """
    if active_themes is None:
        active_themes = list(THEMES_FR.keys())

    raw_text, ok, diag = extract_text_from_bytes(pdf_bytes)

    if not ok or not raw_text.strip():
        return {
            **metadata,
            "extraction_ok":              False,
            "error_msg":                  diag,
            "themes_found":               [],
            "total_passages_with_themes": 0,
            "passages":                   [],
        }

    # Détecter si le texte provient d'un OCR pour activer le nettoyage adapté
    is_ocr = "OCR" in diag

    raw_passages = split_into_passages(raw_text, is_ocr=is_ocr)
    passages     = []

    for (text, page_num, article_ref) in raw_passages:
        themes = classify_passage(text, active_themes)
        if themes:
            dominant = max(themes, key=themes.get)
            passages.append({
                "text":           text[:1000],
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


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRE : DATE DEPUIS NOM DE FICHIER
# ══════════════════════════════════════════════════════════════════════════════

def extract_date_from_filename(filename: str) -> dict:
    """
    Tente d'extraire l'année et le mois depuis un nom de fichier PDF.
    Retourne {"year": str|None, "month": str|None}.
    Formats reconnus : 2023-03, 2023_03, 03-2023, 20230315, mars_2023…
    """
    mois_fr = {
        "janvier": "01", "fevrier":   "02", "mars":     "03", "avril":    "04",
        "mai":     "05", "juin":      "06", "juillet":  "07", "aout":     "08",
        "septembre": "09", "octobre": "10", "novembre": "11", "decembre": "12",
    }
    patterns = [
        (r"(\d{4})[_\-](\d{2})", 1, 2),
        (r"(\d{2})[_\-](\d{4})", 2, 1),
        (r"(\d{4})(\d{2})\d{2}", 1, 2),
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
