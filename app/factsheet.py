"""Printable fact sheet for one plant (standalone HTML, print to PDF from the browser) and QR codes."""
import io
import os
from datetime import date
from html import escape
from urllib.parse import quote, urlsplit, urlunsplit

import qrcode
import qrcode.image.svg
import streamlit as st

from i18n import lang, summary_sentence, t


def app_url() -> str:
    """Public address of the app: APP_URL when set (deployed), else the address the browser used."""
    url = os.getenv("APP_URL") or st.context.url or "http://localhost:8501"
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "", "", "")).rstrip("/")


def qr_svg(url: str, box: int = 6) -> str:
    """QR code as inline SVG (no image library needed)."""
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=box, border=2)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode("utf-8")
    return svg[svg.index("<svg"):]


def profile_url(species: str) -> str:
    return f"{app_url()}/?species={quote(species)}"


def _e(x) -> str:
    return escape("" if x is None or (isinstance(x, float) and x != x) else str(x))


def fact_sheet_html(species, family, local_names, uses, prep_check, reviewed, evidence, flags, sources) -> str:
    """`uses`, `reviewed`, `evidence`, `flags`, `sources` are DataFrames already filtered to this plant."""
    src_by_id = {s.doc_id: s for s in sources.itertuples()}
    use_rows = "".join(
        f"<tr><td>{_e(u.use)}</td><td>{_e(u.part_used)}</td><td>{_e(u.preparation)}</td>"
        f"<td>{_e(t(u.community) if u.community else '')}</td><td>{_e(u.place or u.location)}</td>"
        f"<td>{_e(getattr(src_by_id.get(u.doc_id), 'title', u.doc_id))}"
        f"{', p. ' + _e(int(u.page)) if u.page == u.page and u.page is not None else ''}</td></tr>"
        for u in uses.itertuples())
    reviewed_rows = "".join(
        f"<li><b>{_e(r.title)}</b> ({_e(r.year)}) · {_e(r.preparation)}<br>{_e(r.comparison)} "
        f"<i>{_e(r.limitation)}</i></li>" for r in reviewed.itertuples()) or f"<li>{_e(t('None yet'))}</li>"
    paper_rows = "".join(
        f"<li>{_e(p.title)} ({_e(p.year)}) · PMID {_e(p.pmid)}</li>" for p in evidence.head(8).itertuples())
    flag_rows = "".join(f"<li><b>{_e(f.level)}</b>: {_e(f.note)} <span class='src'>{_e(f.source)}</span></li>"
                        for f in flags.itertuples()) or \
        f"<li>{_e(t('No rule from the limited safety list matched; this is not an all-clear.'))}</li>"
    cites = "".join(f"<li>{_e(s.citation)} · {_e(s.licence)} {_e(s.url)}</li>"
                    for s in sources.itertuples() if s.doc_id in set(uses.doc_id))
    link = profile_url(species)
    return f"""<!doctype html><html lang="{'sq' if lang() == 'sq' else 'en'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{_e(species)} · {_e(t('Plant librarian'))}</title>
<style>
body {{ font-family: Georgia, 'Times New Roman', serif; color:#1f3328; background:#fff; max-width:820px; margin:24px auto;
  padding:0 18px; line-height:1.45; }}
header {{ display:flex; justify-content:space-between; gap:18px; border-bottom:3px solid #2f6b4f; padding-bottom:10px; }}
h1 {{ margin:0; font-size:28px; font-style:italic; }} h2 {{ font-size:17px; color:#2f6b4f; margin:20px 0 6px;
  border-bottom:1px solid #d9ddcf; padding-bottom:3px; }}
.meta {{ color:#52665a; font-size:14px; }} .qr svg {{ width:96px; height:96px; }} .qr div {{ font-size:10px; text-align:center; }}
table {{ width:100%; border-collapse:collapse; font-size:12.5px; }} th, td {{ border:1px solid #d9ddcf; padding:4px 6px;
  text-align:left; vertical-align:top; }} th {{ background:#eef0e6; }}
ul {{ font-size:13px; padding-left:18px; }} .verdict {{ background:#eef0e6; border-radius:8px; padding:8px 10px; font-size:14px; }}
.src {{ color:#6b7f70; font-size:11px; word-break:break-all; }} footer {{ margin-top:22px; font-size:11px; color:#6b7f70;
  border-top:1px solid #d9ddcf; padding-top:8px; }}
@media print {{ body {{ margin:0 auto; }} a {{ color:inherit; text-decoration:none; }} }}
</style></head><body>
<header><div><div class="meta">{_e(t('Plant librarian'))} · EthnoHack 2026</div><h1>{_e(species)}</h1>
<div class="meta">{_e(family or t('Family not listed'))} · {_e(local_names)}</div></div>
<div class="qr">{qr_svg(link, 4)}<div>{_e(t('Open in the app'))}</div></div></header>
<h2>{_e(t('What the study reports'))} ({len(uses)})</h2>
<table><tr><th>{_e(t('Traditional use'))}</th><th>{_e(t('Plant part'))}</th><th>{_e(t('Preparation'))}</th>
<th>{_e(t('Community'))}</th><th>{_e(t('Recorded location'))}</th><th>{_e(t('Study'))}</th></tr>{use_rows}</table>
<h2>{_e(t('Was the same preparation tested?'))}</h2>
<div class="verdict"><b>{_e(t(prep_check['label']))}</b>. {_e(summary_sentence(prep_check))}</div>
<h2>{_e(t('Reviewed papers'))}</h2><ul>{reviewed_rows}</ul>
<h2>{_e(t('PubMed candidates'))} ({len(evidence)})</h2><ul>{paper_rows}</ul>
<h2>{_e(t('Safety and conservation'))}</h2><ul>{flag_rows}</ul>
<h2>{_e(t('Sources'))}</h2><ul>{cites}</ul>
<footer>{_e(t('Traditional-use reports, not proof that a remedy works. Not medical advice.'))} {_e(t('No doses are given.'))}
{_e(t('PubMed candidates are keyword matches, not reviewed conclusions.'))} {_e(t('Generated'))} {date.today().isoformat()} · {_e(link)}</footer>
</body></html>"""
