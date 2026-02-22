"""
core/reporter.py
================
Version adaptée Streamlit : les fonctions retournent des chaînes
ou des structures Python plutôt qu'écrire des fichiers sur disque.
"""

import re
from collections import defaultdict
from datetime import datetime

THEMES_FR = {
    "avifaune":      "Avifaune",
    "chiropteres":   "Chiroptères",
    "zones_humides": "Zones humides",
    "paysage":       "Paysage",
}

MOIS_FR = {
    "01": "Janvier", "02": "Février", "03": "Mars",    "04": "Avril",
    "05": "Mai",     "06": "Juin",    "07": "Juillet", "08": "Août",
    "09": "Septembre","10": "Octobre","11": "Novembre","12": "Décembre",
}


def build_aggregation(results: list[dict]) -> dict:
    """Agrège les résultats par région → année → mois → thème → liste de passages."""
    agg = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    for doc in results:
        if not doc.get("extraction_ok"):
            continue
        region = doc.get("region", "Région inconnue")
        year   = doc.get("year")  or "Année inconnue"
        month  = doc.get("month") or "Mois inconnu"
        doc_ref = (doc.get("text") or "")[:80]

        for p in doc.get("passages", []):
            for theme, score in p.get("themes", {}).items():
                if theme not in THEMES_FR:
                    continue
                agg[region][year][month][theme].append({
                    "doc_ref":     doc_ref,
                    "article_ref": p.get("article_ref"),
                    "page_num":    p.get("page_num"),
                    "score":       score,
                    "text":        (p.get("text") or "")[:600],
                    "url":         doc.get("url", ""),
                    "type_short":  doc.get("type_short", ""),
                    "type_long":   doc.get("type_long",  ""),
                    "type_found":  doc.get("type_found", False),
                })

    import json
    return json.loads(json.dumps(agg))  # convertit les defaultdict en dict


def build_summary_table(agg: dict) -> list[dict]:
    """Construit le tableau de synthèse (une ligne par région × année × mois)."""
    rows = []
    for region, years in sorted(agg.items()):
        for year, months in sorted(years.items()):
            for month, themes in sorted(months.items()):
                # Récupérer les types d'arrêtés présents dans cette cellule
                types_set = set()
                for plist in themes.values():
                    for p in plist:
                        if p.get("type_short"):
                            types_set.add(p["type_short"])
                types_str = ", ".join(sorted(types_set)) if types_set else "—"

                row = {
                    "Région":          region,
                    "Type d'arrêté":   types_str,
                    "Année":           year,
                    "Mois":            MOIS_FR.get(month, month),
                    "Mois_num":        month,
                }
                for th_key, th_label in THEMES_FR.items():
                    row[th_label] = len(themes.get(th_key, []))
                row["Total passages"] = sum(len(v) for v in themes.values())
                rows.append(row)
    return rows


def build_html_report(agg: dict, rows: list[dict],
                      results: list[dict]) -> str:
    """Génère et retourne le rapport HTML complet sous forme de chaîne."""

    total_docs   = len([r for r in results if r.get("extraction_ok")])
    total_pass   = sum(len(r.get("passages", [])) for r in results)
    docs_failed  = len([r for r in results if not r.get("extraction_ok")])

    coverage = {
        th: sum(1 for r in results
                if r.get("extraction_ok") and th in r.get("themes_found", []))
        for th in THEMES_FR
    }

    # ── Extraits HTML ──────────────────────────────────────────────────────
    extracts_html = []
    for region, years in sorted(agg.items()):
        extracts_html.append(f'<div class="region-block"><h2>{region}</h2>')
        by_theme = defaultdict(list)
        for year, months in sorted(years.items()):
            for month, themes in sorted(months.items()):
                for th, plist in themes.items():
                    for p in plist:
                        by_theme[th].append({**p, "year": year,
                                             "month": MOIS_FR.get(month, month)})

        colors = {"avifaune":"#1565C0","chiropteres":"#6A1B9A",
                  "zones_humides":"#00695C","paysage":"#E65100"}

        for th_key, th_label in THEMES_FR.items():
            plist = by_theme.get(th_key, [])
            if not plist:
                continue
            c = colors.get(th_key, "#607D8B")
            extracts_html.append(
                f'<div class="theme-sec">'
                f'<h3 style="border-left:4px solid {c};padding-left:10px">'
                f'{th_label} <span class="badge" style="background:{c}">{len(plist)}</span>'
                f'</h3><div class="cards">'
            )
            for p in sorted(plist, key=lambda x:(x.get("year",""),x.get("month",""))):
                art = f'<span class="art">{p["article_ref"]}</span>' if p.get("article_ref") else ""
                url = f'<a href="{p["url"]}" target="_blank">🔗</a>' if p.get("url") else ""
                txt = (p.get("text","") or "").replace("<","&lt;").replace(">","&gt;")
                extracts_html.append(f"""
                <div class="card">
                  <div class="cmeta"><strong>{p.get("month","")} {p.get("year","")}</strong>
                  {art} p.{p.get("page_num","?")} {url}</div>
                  <div class="cref">{p.get("doc_ref","")[:80]}</div>
                  <blockquote>{txt[:500]}{"…" if len(txt)>500 else ""}</blockquote>
                </div>""")
            extracts_html.append("</div></div>")
        extracts_html.append("</div>")

    # ── Tableau HTML ──────────────────────────────────────────────────────
    trows = ""
    for row in rows:
        cells = "".join(f'<td class="n">{row.get(lbl,0)}</td>' for lbl in THEMES_FR.values())
        trows += (f'<tr><td>{row["Région"]}</td><td>{row["Année"]}</td>'
                  f'<td>{row["Mois"]}</td>{cells}'
                  f'<td class="n tot">{row.get("Total passages",0)}</td></tr>')

    # ── Stats cards ─────────────────────────────────────────────────────
    icons = {"avifaune":"🦅","chiropteres":"🦇","zones_humides":"💧","paysage":"🌄"}
    col   = {"avifaune":"#1565C0","chiropteres":"#6A1B9A",
             "zones_humides":"#00695C","paysage":"#E65100"}
    stat_cards = ""
    for th_key, th_label in THEMES_FR.items():
        n   = coverage.get(th_key, 0)
        pct = round(100*n/total_docs,1) if total_docs else 0
        stat_cards += f"""
        <div class="scard" style="border-top:4px solid {col[th_key]}">
          <div class="sicon">{icons[th_key]}</div>
          <div class="slbl">{th_label}</div>
          <div class="sval">{n} arrêtés</div>
          <div class="spct">{pct}% de couverture</div>
        </div>"""

    gen_date = datetime.now().strftime("%d/%m/%Y à %H:%M")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Arrêtés éoliens — Rapport environnemental</title>
<style>
:root{{--v:#1B4D3E;--vm:#2D7A5F;--cr:#F7F4EE;--bd:#D8D3C8;--txt:#1A1A1A}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Source Serif 4',Georgia,serif;background:var(--cr);color:var(--txt);font-size:14px}}
.hdr{{background:var(--v);color:white;padding:24px 40px}}
.hdr h1{{font-family:Syne,sans-serif;font-size:1.6em;font-weight:800}}
.hdr p{{opacity:.8;font-style:italic;margin-top:4px}}
.cnt{{max-width:1350px;margin:0 auto;padding:24px 20px}}
.meta-bar{{background:white;border:1px solid var(--bd);border-radius:8px;
           padding:12px 18px;margin-bottom:20px;display:flex;gap:28px;
           flex-wrap:wrap;font-size:.88em;color:#666}}
.meta-bar strong{{color:var(--txt)}}
.sgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
        gap:14px;margin-bottom:28px}}
.scard{{background:white;border-radius:10px;padding:18px 14px;text-align:center;
        box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.sicon{{font-size:1.8em;margin-bottom:6px}}
.slbl{{font-size:.8em;color:#666;margin-bottom:4px}}
.sval{{font-size:1.3em;font-weight:700}}
.spct{{font-size:.78em;color:#888;margin-top:2px}}
h2.st{{font-size:1.15em;margin:24px 0 12px;border-bottom:2px solid var(--v);
       padding-bottom:6px;color:var(--v)}}
.tbl-wrap{{overflow-x:auto;background:white;border-radius:10px;
           box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:28px}}
table{{width:100%;border-collapse:collapse;font-size:.87em}}
thead th{{background:var(--v);color:white;padding:9px 11px;text-align:left}}
tbody tr{{border-bottom:1px solid var(--bd)}}
tbody tr:hover{{background:#EEF4FF}}
tbody td{{padding:7px 11px}}
td.n{{text-align:center}}
td.tot{{font-weight:700;background:#F0F4FF}}
.region-block{{background:white;border-radius:10px;
               box-shadow:0 2px 8px rgba(0,0,0,.06);
               margin-bottom:20px;padding:18px 22px}}
.region-block h2{{font-size:1.15em;color:var(--v);margin-bottom:14px;
                  padding-bottom:8px;border-bottom:1px solid var(--bd)}}
.theme-sec{{margin-bottom:18px}}
.theme-sec h3{{font-size:.95em;margin-bottom:10px;display:flex;
               align-items:center;gap:8px}}
.badge{{color:white;font-size:.7em;padding:2px 8px;border-radius:12px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:12px}}
.card{{border:1px solid var(--bd);border-radius:8px;padding:12px 14px;background:#FAFAFA}}
.cmeta{{font-size:.78em;color:#666;margin-bottom:4px}}
.art{{background:#E3F2FD;color:#1565C0;padding:1px 6px;border-radius:3px;font-size:.88em}}
.cref{{font-size:.76em;color:#888;margin-bottom:6px;
       white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
blockquote{{font-size:.84em;line-height:1.6;border-left:3px solid #BDBDBD;
            padding-left:10px;margin:0;font-style:italic;color:#333}}
.filters{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}}
.filters input,.filters select{{border:1px solid var(--bd);border-radius:5px;
                                  padding:6px 10px;font-size:.87em;background:white}}
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Source+Serif+4:ital,wght@0,400;1,300&display=swap');
</style>
</head>
<body>
<div class="hdr">
  <h1>🌬️ Arrêtés préfectoraux éoliens — Analyse environnementale</h1>
  <p>Extraction automatisée · Rapport généré le {gen_date}</p>
</div>
<div class="cnt">
  <div class="meta-bar">
    <span>📄 <strong>{total_docs}</strong> arrêtés analysés</span>
    <span>📝 <strong>{total_pass}</strong> passages thématiques</span>
    <span>⚠️ <strong>{docs_failed}</strong> PDFs non extractibles</span>
    <span>🗂️ <strong>{len(agg)}</strong> région(s)</span>
  </div>
  <div class="sgrid">{stat_cards}</div>

  <h2 class="st">Tableau de synthèse</h2>
  <div class="filters">
    <input type="text" id="fr" placeholder="🔍 Région..." oninput="filt()">
    <input type="text" id="fy" placeholder="🔍 Année..." oninput="filt()">
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>Région</th><th>Année</th><th>Mois</th>
        {"".join(f'<th class="n">{lbl}</th>' for lbl in THEMES_FR.values())}
        <th class="n">Total</th>
      </tr></thead>
      <tbody id="tb">{trows}</tbody>
    </table>
  </div>

  <h2 class="st">Extraits classifiés par région</h2>
  {"".join(extracts_html)}
</div>
<script>
function filt(){{
  const r=document.getElementById('fr').value.toLowerCase();
  const y=document.getElementById('fy').value.toLowerCase();
  document.querySelectorAll('#tb tr').forEach(row=>{{
    const c=row.querySelectorAll('td');
    row.style.display=(c[0].textContent.toLowerCase().includes(r)&&
                       c[1].textContent.toLowerCase().includes(y))?'':'none';
  }});
}}
</script>
</body></html>"""
