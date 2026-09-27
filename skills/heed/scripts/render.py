"""Render .heed/findings.json (+ inventory.json) as a self-contained report (phase 5).

    python3 render.py .heed/findings.json .heed/inventory.json -o .heed/report.html

One HTML file, no server. Nothing loads from the network except web fonts,
which fall back to system fonts offline. Overview first: an attention map in
which every block *is* a finding (no aggregate score), then the findings by
priority, each with its evidence on demand. Evidence levels are drawn
differently: ● confirmed, ◐ observed, ○ inferred.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ORDER = ["urgent", "high", "medium", "watch"]
WEIGHT = {"urgent": 4, "high": 3, "medium": 2, "watch": 1}
BLOCK = {"urgent": 58, "high": 44, "medium": 32, "watch": 22}
GLYPH = {"confirmed": "●", "observed": "◐", "inferred": "○"}
e = lambda s: html.escape(str(s if s is not None else ""))

CSS = """
:root{--paper:#f5f0e6;--ink:#2a2826;--muted:#7a7368;--rule:#d8cfbf;--wash:#ede5d6;--sage:#4f6f58;
--cinnabar:#b8432c;--cwash:#f1ddd3;--ochre:#9c7424;--owash:#efe3c7;
--serif:Newsreader,Georgia,"Times New Roman",serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--paper:#1a1916;--ink:#ebe5d9;--muted:#9c9587;
--rule:#3b3731;--wash:#24221e;--sage:#93b69d;--cinnabar:#e2765c;--cwash:#3a231d;--ochre:#d0a95b;--owash:#33291a}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans)}
main{max-width:920px;margin:0 auto;padding:36px 16px 72px}
.fig{font:500 11px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font:600 38px/1.1 var(--serif);margin:8px 0 8px;letter-spacing:-.01em}
.lede{font:400 18px/1.5 var(--serif);color:var(--muted);margin:0 0 26px;max-width:62ch}
.legend{font:400 12px var(--mono);color:var(--muted);display:flex;gap:18px;flex-wrap:wrap;margin:10px 0 0}
h2{font:400 26px/1.2 var(--serif);margin:40px 0 12px;border-top:1px solid var(--rule);padding-top:22px}
.map{display:grid;grid-template-columns:minmax(0,200px) minmax(0,1fr);gap:0 18px;align-items:start}
.map .lab{font:400 17px var(--serif)}.map .lab small{display:block;font:400 11px var(--mono);color:var(--muted)}
.blocks{display:flex;flex-direction:column;gap:6px}
.item{display:grid;grid-template-columns:62px minmax(0,1fr);gap:10px;align-items:center;text-decoration:none;color:var(--ink)}
.item .t{font:400 14.5px/1.35 var(--sans)}.item .t b{font:500 11px var(--mono);color:var(--muted);margin-right:6px}
.item:hover .t{text-decoration:underline}
.blk{height:20px;border-radius:3px;display:block}
.card:has(details[open]) .top{display:none}
.map .lab,.map .blocks{padding:10px 0;border-top:1px solid var(--rule)}
.blk.urgent{background:var(--cinnabar)}.blk.high{background:var(--ochre)}
.blk.medium{background:var(--ink);opacity:.62}.blk.watch{border:1.5px solid var(--muted);opacity:.7}

.pr{font:600 11px var(--mono);letter-spacing:.12em;text-transform:uppercase}
.pr.urgent{color:var(--cinnabar)}.pr.high{color:var(--ochre)}.pr.medium{color:var(--ink)}.pr.watch{color:var(--muted)}
.card{border-top:1px solid var(--rule);padding:18px 0 20px}.card:target{background:var(--wash);margin:0 -12px;padding:18px 12px 20px}
.card h3{font:400 23px/1.25 var(--serif);margin:6px 0 6px}
.meta{font:400 12px var(--mono);color:var(--muted)}
.sum{font:400 16px/1.55 var(--serif);margin:6px 0 10px;max-width:68ch}
.fm{font:italic 400 15.5px/1.5 var(--serif);color:var(--muted);margin:0 0 10px;max-width:68ch}
.ev{list-style:none;padding:0;margin:6px 0 0}.ev li{display:grid;grid-template-columns:18px 88px minmax(0,1fr);gap:6px;
font:400 14px/1.5 var(--sans);padding:3px 0}
.ev .g{font-size:14px;color:var(--ink)}.ev .k{font:500 11px/1.9 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.ev li.inferred{color:var(--muted);font-style:italic}.ev li.inferred .g{color:var(--muted)}
.ev .loc{display:block;font:400 12px var(--mono);color:var(--muted);font-style:normal;word-break:break-all}
.ev .loc a{color:inherit}.ev pre{margin:4px 0 0;font:400 12px/1.45 var(--mono);background:var(--wash);padding:6px 8px;
white-space:pre-wrap;word-break:break-word;font-style:normal;color:var(--ink)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:10px 0 0}
.cols h4,.card h4{font:500 11px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 4px}
.cols ul{margin:0;padding-left:18px;font:400 14.5px/1.5 var(--sans)}
details summary{cursor:pointer;font:500 13px var(--sans);color:var(--ink);margin-top:8px}
.next{font:400 14.5px/1.5 var(--sans);margin:10px 0 0}.next b{font-weight:600}
.np li{font:400 14.5px/1.5 var(--sans);margin:4px 0}.np .r{color:var(--muted)}
.foot{font:400 12.5px/1.6 var(--mono);color:var(--muted);margin-top:40px;border-top:1px solid var(--rule);padding-top:14px}
@media (max-width:620px){h1{font-size:30px}.map{grid-template-columns:1fr}.map .blocks{border-top:0;padding-top:0}.cols{grid-template-columns:1fr}
.ev li{grid-template-columns:18px minmax(0,1fr)}.ev .k{display:none}}
"""

JS = """
function openTarget(){const el=document.getElementById(location.hash.slice(1));
 if(el){const d=el.querySelector('details');if(d)d.open=true;}}
addEventListener('hashchange',openTarget);openTarget();
"""


def link(web: str | None, commit: str, ev: dict) -> str:
    parts = []
    if ev.get("file"):
        ln = f":{ev['line']}" if ev.get("line") else ""
        ln += f"–{ev['end_line']}" if ev.get("end_line") else ""
        text = e(ev["file"] + ln)
        if web:
            anchor = f"#L{ev['line']}" + (f"-L{ev['end_line']}" if ev.get("end_line") else "") if ev.get("line") else ""
            parts.append(f'<a href="{e(web)}/blob/{e(commit)}/{e(ev["file"])}{anchor}">{text}</a>')
        else:
            parts.append(text)
    if ev.get("commit"):
        c = e(ev["commit"])
        parts.append(f'<a href="{e(web)}/commit/{c}">commit {c[:10]}</a>' if web else f"commit {c[:10]}")
    if ev.get("issue") is not None:
        n = e(ev["issue"])
        parts.append(f'<a href="{e(web)}/issues/{n}">#{n}</a>' if web else f"#{n}")
    if ev.get("url"):
        parts.append(f'<a href="{e(ev["url"])}">{e(ev["url"])}</a>')
    out = f'<span class="loc">{" · ".join(parts)}</span>' if parts else ""
    if "command" in ev:
        out += (f'<span class="loc">$ {e(ev["command"])}  → exit {e(ev.get("exit_code"))}</span>'
                f'<pre>{e(ev.get("output", ""))}</pre>')
    return out


def strongest(ev: list[dict]) -> dict | None:
    for lv in ("confirmed", "observed"):
        for x in ev:
            if x.get("level") == lv:
                return x
    return None


def render(doc: dict, inv: dict | None) -> str:
    repo = doc.get("repo", {})
    inv_repo = (inv or {}).get("repo", {})
    web = repo.get("web") or inv_repo.get("web")
    commit = repo.get("commit") or inv_repo.get("commit") or "HEAD"
    name = repo.get("name") or inv_repo.get("name") or "repository"
    areas = {a["id"]: a for a in doc.get("areas", [])}
    fs = sorted(doc.get("findings", []), key=lambda f: (ORDER.index(f.get("priority", "watch")), f.get("id", "")))
    by_area: dict[str, list] = {}
    for f in fs:
        by_area.setdefault(f["area"], []).append(f)
    area_rows = sorted(by_area.items(), key=lambda kv: -sum(WEIGHT[f["priority"]] for f in kv[1]))
    counts = {p: sum(1 for f in fs if f["priority"] == p) for p in ORDER}
    method = doc.get("method", {})

    out = [f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Heed · {e(name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main>
<div class="fig">Heed · {e(name)} @ {e(commit)} · {e(repo.get("scanned_at", ""))}</div>
<h1>What needs attention in {e(name)}</h1>
<p class="lede">{len(fs)} finding{'s' if len(fs) != 1 else ''} from {e(method.get('candidates_investigated', '?'))} candidates investigated
({', '.join(f'{counts[p]} {p}' for p in ORDER if counts[p])}). Each finding stands on evidence you can check.
{len(doc.get('not_promoted', []))} candidate{'s' if len(doc.get('not_promoted', [])) != 1 else ''} didn't earn a finding; they're listed at the end.</p>
"""]
    # attention map
    out.append('<div class="map">')
    for aid, items in area_rows:
        a = areas.get(aid, {"label": aid, "path": ""})
        blocks = "".join(
            f'<a class="item" href="#{e(f["id"])}"><span class="blk {f["priority"]}" style="width:{BLOCK[f["priority"]]}px"></span>'
            f'<span class="t"><b>{e(f["id"])}</b>{e(f["title"])}</span></a>' for f in items)
        out.append(f'<div class="lab">{e(a.get("label", aid))}<small>{e(a.get("path", ""))}</small></div>'
                   f'<div class="blocks">{blocks}</div>')
    out.append("</div>")
    out.append('<div class="legend"><span><span class="pr urgent">■</span> urgent</span>'
               '<span><span class="pr high">■</span> high</span><span><span class="pr medium">■</span> medium</span>'
               '<span><span class="pr watch">□</span> watch</span><span>block width = priority; one block per finding</span>'
               '<span>● confirmed · ◐ observed · ○ inferred</span></div>')

    for p in ORDER:
        group = [f for f in fs if f["priority"] == p]
        if not group:
            continue
        out.append(f'<h2><span class="pr {p}">{p}</span></h2>')
        for f in group:
            a = areas.get(f["area"], {"label": f["area"]})
            ev = f.get("evidence", [])
            top = strongest(ev)
            n = {lv: sum(1 for x in ev if x.get("level") == lv) for lv in GLYPH}
            tally = " · ".join(f"{GLYPH[lv]} {n[lv]} {lv}" for lv in GLYPH if n[lv])
            items = "".join(
                f'<li class="{e(x.get("level"))}"><span class="g">{GLYPH.get(x.get("level"), "?")}</span>'
                f'<span class="k">{e(x.get("kind"))}</span><span>{e(x.get("claim"))}{link(web, commit, x)}</span></li>'
                for x in sorted(ev, key=lambda x: list(GLYPH).index(x.get("level", "inferred"))))
            lists = ""
            if f.get("impact") or f.get("why_now"):
                ul = lambda xs: "<ul>" + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul>" if xs else "<p class='meta'>none stated</p>"
                lists = (f'<div class="cols"><div><h4>Impact</h4>{ul(f.get("impact", []))}</div>'
                         f'<div><h4>Why now</h4>{ul(f.get("why_now", []))}</div></div>')
            out.append(f"""<section class="card" id="{e(f['id'])}">
<div class="meta"><span class="pr {p}">{p}</span> · {e(a.get('label'))} · {e(f['id'])}</div>
<h3>{e(f['title'])}</h3>
<p class="sum">{e(f.get('summary'))}</p>
{f'<p class="fm">Failure mode: {e(f["failure_mode"])}</p>' if f.get('failure_mode') else ''}
{f'<ul class="ev top"><li class="{e(top.get("level"))}"><span class="g">{GLYPH[top["level"]]}</span><span class="k">{e(top.get("kind"))}</span><span>{e(top.get("claim"))}{link(web, commit, top)}</span></li></ul>' if top else ''}
<details><summary>Evidence ({tally})</summary><ul class="ev">{items}</ul>{lists}</details>
{f'<p class="next"><b>Next step.</b> {e(f["next_step"])}</p>' if f.get('next_step') else ''}
</section>""")

    np = doc.get("not_promoted", [])
    if np:
        out.append('<h2>Checked and set aside</h2><ul class="np">' + "".join(
            f'<li>{e(x["title"])} <span class="r">— {e(x["reason"])}</span></li>' for x in np) + "</ul>")

    foot = [f"{e(name)} @ {e(commit)}"]
    if inv:
        s, g = inv.get("structure", {}), inv.get("git", {})
        foot.append(f"{s.get('tracked_files', '?')} tracked files · {g.get('commits_90d', '?')} commits in 90 days · "
                    f"{inv.get('markers', {}).get('count', '?')} TODO-style markers · "
                    f"{inv.get('tests', {}).get('test_files', '?')} test files · "
                    f"{len(inv.get('issues', {}).get('open', []))} open issues")
    if method.get("notes"):
        foot.append(e(method["notes"]))
    foot.append("Generated by Heed. Findings are an agent's investigation; evidence marked ○ is reasoning, not fact.")
    out.append(f'<p class="foot">{"<br>".join(foot)}</p></main><script>{JS}</script></body></html>')
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: render.py findings.json [inventory.json] -o report.html")
        return 2
    outp = Path(argv[argv.index("-o") + 1]) if "-o" in argv else Path("report.html")
    pos = [a for i, a in enumerate(argv) if not a.startswith("-") and (i == 0 or argv[i - 1] != "-o")]
    doc = json.loads(Path(pos[0]).read_text())
    inv = json.loads(Path(pos[1]).read_text()) if len(pos) > 1 else None
    outp.write_text(render(doc, inv))
    print(f"wrote {outp}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
