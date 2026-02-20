"""
core/demo_data.py
=================
Données de démonstration pré-chargées pour l'application Streamlit.
Représentatives des prescriptions réelles des arrêtés éoliens français.
"""

DEMO_RESULTS = [
  {
    "url": "https://www.hauts-de-france.developpement-durable.gouv.fr/IMG/pdf/ap_artois_2023-03.pdf",
    "text": "AP Parc Éolien Les Crêtes d'Artois — Préfecture du Pas-de-Calais",
    "filename": "ap_artois_2023-03.pdf",
    "region": "Hauts-de-France",
    "year": "2023", "month": "03",
    "downloaded": True, "extraction_ok": True, "error_msg": "",
    "themes_found": ["avifaune", "chiropteres", "paysage"],
    "total_passages_with_themes": 4,
    "passages": [
      {
        "text": "Article 4.1 — Avifaune. L'exploitant met en place un système de bridage automatique des éoliennes lors des périodes de migration active des rapaces et des grands migrateurs. Ce bridage avifaune est activé au minimum du 15 mars au 15 mai et du 1er septembre au 15 novembre. Un suivi ornithologique annuel est réalisé par un bureau d'études spécialisé, portant sur les espèces nicheuses (nicheur probable et certain dans un rayon de 500 m), les espèces migratoires en transit et les espèces hivernantes. Un bilan ornithologique est transmis à la DREAL chaque année avant le 31 mars. En cas de détection d'un Milan royal ou d'un Busard cendré à moins de 200 m des éoliennes, l'arrêt immédiat de la machine est obligatoire.",
        "page_num": 6, "article_ref": "Article 4.1",
        "themes": {"avifaune": 22}, "dominant_theme": "avifaune"
      },
      {
        "text": "Article 4.2 — Chiroptères. Un bridage acoustique est mis en place sur l'ensemble des éoliennes du parc. Ce bridage chiroptères est activé automatiquement dès que la vitesse de vent est inférieure à 6 m/s et que la température est supérieure à 10°C, entre le coucher et le lever du soleil, du 1er avril au 31 octobre. Des détecteurs ultrasoniques sont installés en nacelle pour le suivi de l'activité chiroptérologique. Le suivi des chiroptères (pipistrelle commune, noctule de Leisler, sérotine commune) est réalisé annuellement selon le protocole SFEPM.",
        "page_num": 7, "article_ref": "Article 4.2",
        "themes": {"chiropteres": 24}, "dominant_theme": "chiropteres"
      },
      {
        "text": "Article 5.1 — Insertion paysagère. Le pétitionnaire veille à l'intégration paysagère des éoliennes dans leur environnement. Un traitement visuel des plateformes est réalisé par un paysagiste agréé. Des photomontages sont réalisés depuis les monuments historiques situés dans l'aire d'étude paysagère, notamment depuis le château d'Olhain (site classé) et depuis les points de covisibilité identifiés dans l'étude d'impact. La hauteur des mâts ne peut excéder 150 m en bout de pale. Le balisage diurne et nocturne respecte la réglementation DGAC en vigueur.",
        "page_num": 9, "article_ref": "Article 5.1",
        "themes": {"paysage": 16}, "dominant_theme": "paysage"
      },
      {
        "text": "Article 3.4 — Mesures compensatoires. En phase de chantier, les habitats de faune et les espèces protégées font l'objet d'un suivi par un écologue. Les travaux de terrassement sont interdits entre le 15 avril et le 31 juillet en présence d'espèces nicheuses avérées à moins de 200 m. Un suivi ornithologique de phase travaux est réalisé hebdomadairement.",
        "page_num": 5, "article_ref": "Article 3.4",
        "themes": {"avifaune": 10}, "dominant_theme": "avifaune"
      }
    ]
  },
  {
    "url": "https://www.hauts-de-france.developpement-durable.gouv.fr/IMG/pdf/ap_thierache_2023-07.pdf",
    "text": "AP Parc Éolien de la Thiérache Verte — Préfecture de l'Aisne",
    "filename": "ap_thierache_2023-07.pdf",
    "region": "Hauts-de-France",
    "year": "2023", "month": "07",
    "downloaded": True, "extraction_ok": True, "error_msg": "",
    "themes_found": ["avifaune", "chiropteres", "zones_humides", "paysage"],
    "total_passages_with_themes": 3,
    "passages": [
      {
        "text": "Article 6.1 — Zones humides. Le dossier comprend un diagnostic pédologique et floristique réalisé selon la méthodologie nationale de délimitation des zones humides. Trois zones humides avérées ont été identifiées dans l'aire d'étude rapprochée, représentant 2,3 ha. Conformément à la loi sur l'eau (IOTA), une compensation zones humides est mise en place selon un ratio de 2 pour 1. La recréation de zone humide est réalisée sur une parcelle de 4,6 ha. Le SDAGE Artois-Picardie est respecté.",
        "page_num": 8, "article_ref": "Article 6.1",
        "themes": {"zones_humides": 28}, "dominant_theme": "zones_humides"
      },
      {
        "text": "Article 4.1 — Avifaune et chiroptères. Le bridage avifaune est activé pendant les migrations prénuptiale et postnuptiale. Un suivi ornithologique spécifique à la Grue cendrée est mis en place, compte tenu du couloir migratoire identifié. Pour les chiroptères, le bridage acoustique est paramétré selon les recommandations de la SFEPM. L'activité chiroptérologique est suivie avec des détecteurs ultrasoniques haute sensibilité.",
        "page_num": 6, "article_ref": "Article 4.1",
        "themes": {"avifaune": 14, "chiropteres": 12}, "dominant_theme": "avifaune"
      },
      {
        "text": "Article 5.2 — Paysage et patrimoine. L'étude de covisibilité avec les monuments historiques révèle 4 points de vue significatifs depuis le secteur de Guise. Des photomontages sont transmis à l'ABF pour avis. Des mesures paysagères spécifiques incluent la plantation de haies bocagères à l'est du parc sur 800 m. L'impact visuel résiduel est qualifié de modéré dans l'étude d'impact.",
        "page_num": 10, "article_ref": "Article 5.2",
        "themes": {"paysage": 18}, "dominant_theme": "paysage"
      }
    ]
  },
  {
    "url": "https://www.grand-est.developpement-durable.gouv.fr/IMG/pdf/ap_champagne_2022-11.pdf",
    "text": "AP Extension Parc Éolien de Champagne — Préfecture de la Marne",
    "filename": "ap_champagne_2022-11.pdf",
    "region": "Grand-Est",
    "year": "2022", "month": "11",
    "downloaded": True, "extraction_ok": True, "error_msg": "",
    "themes_found": ["avifaune", "chiropteres", "zones_humides"],
    "total_passages_with_themes": 3,
    "passages": [
      {
        "text": "Article 4 — Protection de l'avifaune. L'exploitant installe un système de caméras thermiques couplé à un algorithme de détection automatique des oiseaux. Ce système déclenche un arrêt d'urgence des éoliennes lorsqu'un rapace de grande envergure (Milan royal, Aigle botté, Cigogne blanche) est détecté à moins de 300 m de l'éolienne la plus proche. Un rapport annuel de mortalité avifaune est transmis à la DREAL avant le 31 mars.",
        "page_num": 5, "article_ref": "Article 4",
        "themes": {"avifaune": 18}, "dominant_theme": "avifaune"
      },
      {
        "text": "Article 5 — Chiroptères. Le bridage chiroptères est défini par modélisation du risque selon la méthode EUROBATS. Le protocole de bridage acoustique prévoit l'arrêt des éoliennes lorsque l'activité de la Noctule commune ou de la Pipistrelle de Nathusius dépasse 30 contacts par nuit. Des gîtes potentiels de Vespertilion à moustaches ont été identifiés à 450 m du site. Un périmètre de protection de 200 m est maintenu autour de ces gîtes pendant l'hibernation.",
        "page_num": 7, "article_ref": "Article 5",
        "themes": {"chiropteres": 20}, "dominant_theme": "chiropteres"
      },
      {
        "text": "Article 6 — Zones humides. L'autorisation loi sur l'eau est accordée (IOTA). Le projet impacte 0,8 ha de prairie humide à jonçaie. La compensation zones humides est réalisée par recréation de roselière et de mégaphorbiaie sur 1,6 ha. Un diagnostic pédologique complémentaire est réalisé lors des travaux. Le SAGE de la Marne est respecté. La nappe phréatique est surveillée par des piézomètres.",
        "page_num": 9, "article_ref": "Article 6",
        "themes": {"zones_humides": 22}, "dominant_theme": "zones_humides"
      }
    ]
  },
  {
    "url": "https://www.normandie.developpement-durable.gouv.fr/IMG/pdf/ap_bessin_2023-09.pdf",
    "text": "AP Parc Éolien du Bessin — Préfecture du Calvados",
    "filename": "ap_bessin_2023-09.pdf",
    "region": "Normandie",
    "year": "2023", "month": "09",
    "downloaded": True, "extraction_ok": True, "error_msg": "",
    "themes_found": ["avifaune", "chiropteres", "zones_humides", "paysage"],
    "total_passages_with_themes": 3,
    "passages": [
      {
        "text": "Article 7 — Zones humides. La zone d'implantation inclut 1,4 ha de prairies humides à joncs et 0,6 ha de mares agricoles (zones humides avérées). La compensation zones humides est réalisée selon un ratio 3:1 (6 ha recréés) sur des parcelles identifiées par la DDT du Calvados. Un suivi hydraulique par piézomètres est mis en place pendant 5 ans. Les fossés drainants intersectés par les pistes sont busés avec des passages à faune appropriés.",
        "page_num": 11, "article_ref": "Article 7",
        "themes": {"zones_humides": 26}, "dominant_theme": "zones_humides"
      },
      {
        "text": "Article 5 — Paysage côtier. L'étude paysagère prend en compte la sensibilité du paysage côtier normand. Des simulations visuelles depuis les plages du Débarquement (sites mémoriaux protégés) attestent d'une absence de covisibilité directe. Des haies bocagères sont replantées le long des voies d'accès. Le balisage nocturne est synchronisé pour minimiser la gêne visuelle.",
        "page_num": 9, "article_ref": "Article 5",
        "themes": {"paysage": 14}, "dominant_theme": "paysage"
      },
      {
        "text": "Article 4 — Faune volante. Le suivi ornithologique annuel porte sur le Busard Saint-Martin et le Courlis cendré, espèces nicheuses. Le bridage avifaune est activé en période de migration. Le bridage acoustique pour les chiroptères prévoit l'arrêt des éoliennes à faible vent (< 5,5 m/s) entre avril et octobre, de nuit. L'activité chiroptérologique est suivie par des enregistreurs ultrasoniques en nacelle.",
        "page_num": 7, "article_ref": "Article 4",
        "themes": {"avifaune": 12, "chiropteres": 14}, "dominant_theme": "chiropteres"
      }
    ]
  },
  {
    "url": "https://www.nouvelle-aquitaine.developpement-durable.gouv.fr/IMG/pdf/ap_gascogne_2023-04.pdf",
    "text": "AP Parc Éolien des Landes de Gascogne — Préfecture des Landes",
    "filename": "ap_gascogne_2023-04.pdf",
    "region": "Nouvelle-Aquitaine",
    "year": "2023", "month": "04",
    "downloaded": True, "extraction_ok": True, "error_msg": "",
    "themes_found": ["chiropteres", "zones_humides", "paysage"],
    "total_passages_with_themes": 3,
    "passages": [
      {
        "text": "Article 4 — Chiroptères. Les Landes de Gascogne constituent l'un des habitats les plus favorables aux chiroptères forestiers. Dix espèces ont été recensées, dont le Grand Murin, la Barbastelle d'Europe et le Minioptère de Schreibers, toutes inscrites à l'annexe IV de la directive Habitats Faune Flore. Le bridage acoustique est activé dès que la vitesse de vent est inférieure à 8 m/s. Des transects sont réalisés mensuellement entre avril et octobre.",
        "page_num": 6, "article_ref": "Article 4",
        "themes": {"chiropteres": 26}, "dominant_theme": "chiropteres"
      },
      {
        "text": "Article 6 — Zones humides. Le massif des Landes comprend de nombreuses zones humides associées aux nappes superficielles. Le diagnostic pédologique a délimité 3,1 ha de zones humides avérées dans l'emprise du projet. L'autorisation IOTA (rubrique 3.3.1.0) est accordée. La compensation zones humides est réalisée par restauration de mouillers (mares forestières landaises) sur 6,2 ha selon un ratio 2:1.",
        "page_num": 8, "article_ref": "Article 6",
        "themes": {"zones_humides": 24}, "dominant_theme": "zones_humides"
      },
      {
        "text": "Article 7 — Paysage. Le parc s'implante dans un massif forestier géré, à l'écart des zones d'habitat. Depuis la route des Crêtes (itinéraire touristique classé), une intervisibilité partielle avec les éoliennes a été identifiée. Des mesures paysagères incluent la replantation de lisières forestières au nord du parc sur 500 m linéaires. Le balisage nocturne est synchronisé.",
        "page_num": 10, "article_ref": "Article 7",
        "themes": {"paysage": 14}, "dominant_theme": "paysage"
      }
    ]
  },
  {
    "url": "https://www.normandie.developpement-durable.gouv.fr/IMG/pdf/ap_eure_scanne.pdf",
    "text": "AP Parc Éolien de l'Eure — PDF scanné",
    "filename": "ap_eure_scanne.pdf",
    "region": "Normandie",
    "year": "2022", "month": "03",
    "downloaded": True,
    "extraction_ok": False,
    "error_msg": "PDF scanné ou texte non extractible (OCR nécessaire)",
    "themes_found": [], "total_passages_with_themes": 0, "passages": []
  }
]
