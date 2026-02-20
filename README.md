# 🌬️ DREAL Éolien — Application Streamlit
## Analyse automatisée des thématiques environnementales dans les arrêtés préfectoraux

---

## Déploiement en 4 étapes sur Streamlit Cloud (gratuit)

### Étape 1 — Préparer un compte GitHub

Si vous n'avez pas de compte GitHub, créez-en un gratuitement sur github.com.
C'est indispensable : Streamlit Cloud déploie directement depuis GitHub.

### Étape 2 — Créer un dépôt GitHub et y pousser ces fichiers

Créez un nouveau dépôt public (ou privé) sur GitHub, puis uploadez tous ces
fichiers en conservant **exactement la structure suivante** :

```
votre-repo/
├── app.py                ← Point d'entrée Streamlit (NE PAS RENOMMER)
├── requirements.txt      ← Dépendances Python
├── core/
│   ├── __init__.py
│   ├── extractor.py      ← Extraction et classification
│   ├── reporter.py       ← Génération des rapports
│   └── demo_data.py      ← Données de démonstration
```

Via l'interface GitHub, cliquez sur "Add file > Upload files" et glissez-déposez
tous les fichiers. Veillez à recréer le sous-dossier `core/` manuellement.

### Étape 3 — Connecter à Streamlit Cloud

1. Allez sur **share.streamlit.io** et connectez-vous avec GitHub.
2. Cliquez sur **"New app"**.
3. Sélectionnez votre dépôt et la branche (généralement `main`).
4. Dans le champ "Main file path", entrez **`app.py`**.
5. Cliquez sur **"Deploy!"**.

Streamlit installe automatiquement les dépendances listées dans
`requirements.txt`, puis lance l'application. Comptez 2 à 5 minutes.

### Étape 4 — Partager l'URL

Une fois déployée, Streamlit vous fournit une URL publique du type
`https://votre-app-name.streamlit.app`. Partagez cette URL à vos collègues :
ils pourront utiliser l'application directement dans leur navigateur, sans
installer Python ni aucune dépendance.

---

## Utilisation de l'application

L'application propose deux modes d'utilisation :

**Mode démo** : cliquez sur "Charger la démo" pour explorer l'interface avec
des données représentatives d'arrêtés éoliens réels. Idéal pour tester les
fonctionnalités avant de traiter vos propres fichiers.

**Mode analyse** : dans la barre latérale gauche, sélectionnez la région et
(optionnellement) l'année et le mois. Déposez ensuite vos PDFs d'arrêtés dans
la zone de dépôt, puis cliquez sur "Analyser". Les PDFs doivent être
**nativement numériques** (c'est-à-dire issus d'une frappe ou d'une impression
numérique, pas d'un scan). Les PDFs scannés nécessitent une étape OCR préalable.

---

## Limites de Streamlit Cloud (offre gratuite)

L'offre gratuite impose une mémoire de 1 Go par application. Pour traiter
de très gros volumes (plusieurs dizaines de PDFs lourds en une session), il
peut être nécessaire de passer sur un hébergement payant ou d'utiliser un
serveur dédié avec plus de RAM.

Les sessions s'endorment après 7 jours d'inactivité, mais se réactivent
automatiquement lors de la prochaine visite (délai de réveil de ~30 secondes).

---

## Traitement des PDFs scannés (OCR)

Pour les arrêtés publiés en format image (scan), une étape OCR est nécessaire
avant d'utiliser l'application. La solution recommandée est d'utiliser
**OCRmyPDF** en ligne de commande sur votre machine avant d'uploader les fichiers :

```bash
pip install ocrmypdf
ocrmypdf --language fra input_scanne.pdf output_numerique.pdf
```

Le fichier `output_numerique.pdf` sera ensuite directement analysable par l'application.
