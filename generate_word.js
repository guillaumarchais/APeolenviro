const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, Footer, Header, TabStopType, TabStopPosition,
  VerticalAlign, PageBreak
} = require('docx');
const fs = require('fs');

// Données injectées par Python via stdin
const data = JSON.parse(fs.readFileSync('/tmp/word_data.json', 'utf8'));

// ── Palette couleurs thèmes ────────────────────────────────────────────────
const THEME_COLORS = {
  avifaune:      { hex: "1D4ED8", light: "DBEAFE", label: "🦅 Avifaune" },
  chiropteres:   { hex: "7C3AED", light: "EDE9FE", label: "🦇 Chiroptères" },
  zones_humides: { hex: "0F766E", light: "CCFBF1", label: "💧 Zones humides" },
  paysage:       { hex: "C2410C", light: "FFEDD5", label: "🌄 Paysage" },
};

const THEME_LABELS = {
  avifaune:      "Avifaune",
  chiropteres:   "Chiroptères",
  zones_humides: "Zones humides",
  paysage:       "Paysage",
};

// ── Helpers ────────────────────────────────────────────────────────────────
function makeBorder(color = "D1D5DB") {
  return { style: BorderStyle.SINGLE, size: 1, color };
}
function allBorders(color = "D1D5DB") {
  const b = makeBorder(color);
  return { top: b, bottom: b, left: b, right: b };
}

function emptyPara(spacing = 80) {
  return new Paragraph({ spacing: { after: spacing } });
}

function scoreStars(score) {
  return "●".repeat(Math.min(Math.floor(score / 4) + 1, 5));
}

// ── Page de garde ──────────────────────────────────────────────────────────
function makeCoverPage(meta) {
  const children = [];

  // Espace avant le titre
  for (let i = 0; i < 4; i++) children.push(emptyPara(200));

  // Titre principal
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({
      text: "Analyse environnementale",
      bold: true, size: 52, font: "Arial", color: "166534",
    })],
  }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [new TextRun({
      text: "Arrêtés préfectoraux éoliens",
      bold: true, size: 36, font: "Arial", color: "374151",
    })],
  }));

  // Ligne de séparation
  children.push(new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "166534", space: 1 } },
    spacing: { after: 400 },
  }));

  // Métadonnées
  const metaLines = [
    ["Région",    meta.region || "Non spécifiée"],
    ["Documents", String(meta.nb_docs)],
    ["Extraits",  String(meta.nb_passages)],
    ["Généré le", new Date().toLocaleDateString("fr-FR", { day:"2-digit", month:"long", year:"numeric" })],
  ];
  for (const [label, value] of metaLines) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 120 },
      children: [
        new TextRun({ text: label + " : ", bold: true, size: 24, font: "Arial", color: "6B7280" }),
        new TextRun({ text: value, size: 24, font: "Arial", color: "111827" }),
      ],
    }));
  }

  // Saut de page final
  children.push(new Paragraph({ children: [new PageBreak()] }));
  return children;
}

// ── Sommaire textuel ───────────────────────────────────────────────────────
function makeSummaryPage(results) {
  const children = [];

  children.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 0, after: 300 },
    children: [new TextRun({ text: "Synthèse par thématique", font: "Arial", size: 32, bold: true, color: "166534" })],
  }));

  // Tableau récapitulatif
  const themeStats = {};
  for (const doc of results) {
    for (const p of (doc.passages || [])) {
      for (const [th, score] of Object.entries(p.themes || {})) {
        if (!themeStats[th]) themeStats[th] = { count: 0, docs: new Set(), maxScore: 0 };
        themeStats[th].count++;
        themeStats[th].docs.add(doc.filename || doc.text || "");
        themeStats[th].maxScore = Math.max(themeStats[th].maxScore, score);
      }
    }
  }

  const headerRow = new TableRow({
    tableHeader: true,
    children: ["Thématique", "Passages", "Documents", "Score max"].map(h =>
      new TableCell({
        borders: allBorders("166534"),
        shading: { fill: "166534", type: ShadingType.CLEAR },
        width: { size: [2500, 1800, 2700, 2000][["Thématique","Passages","Documents","Score max"].indexOf(h)], type: WidthType.DXA },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({ text: h, bold: true, color: "FFFFFF", font: "Arial", size: 20 })],
        })],
      })
    ),
  });

  const dataRows = Object.entries(THEME_LABELS).map(([key, label]) => {
    const s = themeStats[key] || { count: 0, docs: new Set(), maxScore: 0 };
    const color = THEME_COLORS[key]?.hex || "374151";
    return new TableRow({
      children: [
        [label, color],
        [String(s.count), "374151"],
        [String(s.docs.size), "374151"],
        [s.maxScore > 0 ? `${s.maxScore} ${scoreStars(s.maxScore)}` : "—", "374151"],
      ].map(([text, col], ci) =>
        new TableCell({
          borders: allBorders("D1D5DB"),
          shading: { fill: ci === 0 ? THEME_COLORS[key]?.light || "F9FAFB" : "FFFFFF", type: ShadingType.CLEAR },
          width: { size: [2500, 1800, 2700, 2000][ci], type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({ text, font: "Arial", size: 20, bold: ci === 0, color: col })],
          })],
        })
      ),
    });
  });

  children.push(new Table({
    width: { size: 9000, type: WidthType.DXA },
    columnWidths: [2500, 1800, 2700, 2000],
    rows: [headerRow, ...dataRows],
  }));

  children.push(emptyPara(300));
  children.push(new Paragraph({ children: [new PageBreak()] }));
  return children;
}

// ── Section d'un thème ─────────────────────────────────────────────────────
function makeThemeSection(themeKey, results) {
  const color   = THEME_COLORS[themeKey] || { hex: "374151", light: "F9FAFB" };
  const label   = THEME_LABELS[themeKey] || themeKey;
  const children = [];

  // Titre de section thème
  children.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 200, after: 200 },
    children: [new TextRun({
      text: label,
      font: "Arial", size: 32, bold: true, color: color.hex,
    })],
  }));

  // Ligne colorée sous le titre
  children.push(new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: color.hex, space: 1 } },
    spacing: { after: 300 },
  }));

  // Collecter tous les passages du thème, triés par score décroissant
  const allPassages = [];
  for (const doc of results) {
    for (const p of (doc.passages || [])) {
      if (p.themes && p.themes[themeKey]) {
        allPassages.push({
          ...p,
          _score: p.themes[themeKey],
          _doc: doc.text || doc.filename || "Document inconnu",
          _region: doc.region || "",
          _date: (doc.month && doc.year) ? `${doc.month}/${doc.year}` : (doc.year || ""),
        });
      }
    }
  }
  allPassages.sort((a, b) => b._score - a._score);

  if (allPassages.length === 0) {
    children.push(new Paragraph({
      children: [new TextRun({ text: "Aucun extrait détecté pour ce thème.", font: "Arial", size: 22, color: "6B7280", italics: true })],
    }));
    children.push(new Paragraph({ children: [new PageBreak()] }));
    return children;
  }

  // Grouper par document
  const byDoc = {};
  for (const p of allPassages) {
    const key = p._doc;
    if (!byDoc[key]) byDoc[key] = { meta: p, passages: [] };
    byDoc[key].passages.push(p);
  }

  for (const [docName, { meta, passages }] of Object.entries(byDoc)) {
    // Sous-titre document
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 240, after: 120 },
      children: [new TextRun({
        text: docName.substring(0, 100),
        font: "Arial", size: 24, bold: true, color: "374151",
      })],
    }));

    if (meta._region || meta._date) {
      children.push(new Paragraph({
        spacing: { after: 160 },
        children: [new TextRun({
          text: [meta._region, meta._date].filter(Boolean).join(" · "),
          font: "Arial", size: 18, color: "6B7280", italics: true,
        })],
      }));
    }

    for (const p of passages) {
      // Bandeau article + score
      const artRef  = p.article_ref ? `${p.article_ref}  ` : "";
      const allThemes = Object.entries(p.themes || {})
        .map(([k]) => THEME_LABELS[k] || k).join(" · ");

      children.push(new Paragraph({
        spacing: { before: 100, after: 60 },
        children: [
          artRef ? new TextRun({ text: artRef, font: "Courier New", size: 18, bold: true, color: color.hex }) : null,
          new TextRun({ text: allThemes, font: "Arial", size: 18, color: color.hex, bold: true }),
          new TextRun({ text: `   Score : ${p._score} ${scoreStars(p._score)}`, font: "Arial", size: 18, color: "6B7280" }),
        ].filter(Boolean),
      }));

      // Texte de l'extrait dans un cadre coloré (cellule de tableau 1×1)
      const textContent = (p.text || "").replace(/\s+/g, " ").trim();
      children.push(new Table({
        width: { size: 9000, type: WidthType.DXA },
        columnWidths: [9000],
        rows: [new TableRow({
          children: [new TableCell({
            borders: {
              top:    { style: BorderStyle.SINGLE, size: 1, color: color.hex },
              bottom: { style: BorderStyle.SINGLE, size: 1, color: color.hex },
              left:   { style: BorderStyle.THICK,  size: 6, color: color.hex },
              right:  { style: BorderStyle.SINGLE, size: 1, color: "D1D5DB" },
            },
            shading: { fill: color.light, type: ShadingType.CLEAR },
            width: { size: 9000, type: WidthType.DXA },
            margins: { top: 120, bottom: 120, left: 200, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({
                text: textContent,
                font: "Arial", size: 20, color: "111827",
              })],
            })],
          })],
        })],
      }));
      children.push(emptyPara(120));
    }
  }

  // Saut de page entre thèmes
  children.push(new Paragraph({ children: [new PageBreak()] }));
  return children;
}

// ── Document principal ─────────────────────────────────────────────────────
const meta = {
  region:      data.region || "Non spécifiée",
  nb_docs:     data.results.length,
  nb_passages: data.results.reduce((s, d) => s + (d.passages || []).length, 0),
};

const allChildren = [
  ...makeCoverPage(meta),
  ...makeSummaryPage(data.results),
];

for (const themeKey of ["avifaune", "chiropteres", "zones_humides", "paysage"]) {
  allChildren.push(...makeThemeSection(themeKey, data.results));
}

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run:       { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run:       { size: 24, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size:   { width: 11906, height: 16838 },   // A4
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 }, // 2 cm
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "DREAL Éolien — Analyse environnementale  |  Page ", font: "Arial", size: 16, color: "9CA3AF" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "9CA3AF" }),
            new TextRun({ text: " / ", font: "Arial", size: 16, color: "9CA3AF" }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 16, color: "9CA3AF" }),
          ],
        })],
      }),
    },
    children: allChildren,
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(process.argv[2] || '/tmp/rapport_eolien.docx', buffer);
  console.log("OK");
}).catch(e => { console.error(e); process.exit(1); });
