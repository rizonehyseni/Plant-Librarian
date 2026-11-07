"""Shared look for every page: one stylesheet, page headers and icons.

Colours and fonts live in .streamlit/config.toml. Icons are Google Material Symbols
(https://fonts.google.com/icons): Streamlit renders ":material/<name>:" in text, and the
page headers load the same icon font for their HTML.
"""
from html import escape
from pathlib import Path

import streamlit as st

from i18n import t

ASSETS = Path(__file__).resolve().parent / "assets"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0&display=block');
.block-container { max-width: 1180px; padding-top: 4.6rem; padding-bottom: 5rem; }
.eh-ms { font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal;
  line-height: 1; letter-spacing: normal; text-transform: none; white-space: nowrap;
  -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }

.eh-header { display: flex; gap: 18px; align-items: center; margin: 0 0 1.6rem; }
.eh-header .eh-icon { width: 54px; height: 54px; border-radius: 15px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(140deg, #2f6b4f 0%, #4f8a63 100%);
  box-shadow: 0 8px 18px rgba(31, 61, 46, .18); }
.eh-header .eh-icon .eh-ms { color: #f7f5ee; font-size: 30px; }
.eh-eyebrow { font-size: .72rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase;
  color: #6b7f70; margin: 0 0 2px; }
.eh-title { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 2.15rem;
  line-height: 1.12; letter-spacing: -.02em; color: #1f3328; margin: 0; }
.eh-sub { color: #52665a; margin: 6px 0 0; max-width: 760px; font-size: 1rem; line-height: 1.5; }

.eh-hero { position: relative; overflow: hidden; border-radius: 22px; padding: 34px 38px;
  margin: 0 0 1.8rem; color: #f7f5ee;
  background: radial-gradient(circle at 88% 12%, rgba(255,255,255,.12) 0, transparent 38%),
              linear-gradient(125deg, #1d4433 0%, #2f6b4f 62%, #4f8a63 100%);
  box-shadow: 0 14px 34px rgba(31, 61, 46, .18); }
.eh-hero .eh-eyebrow { color: #c9dccb; }
.eh-hero .eh-title { color: #fffdf6; font-size: 2.6rem; }
.eh-hero .eh-sub { color: #e3ece0; font-size: 1.05rem; }
.eh-hero .eh-leaf { position: absolute; right: 26px; bottom: -26px; font-size: 168px; color: rgba(255,255,255,.08); }
.eh-hero .eh-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.eh-hero .eh-chip { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.18); font-size: .82rem; color: #f7f5ee; }
.eh-hero .eh-chip .eh-ms { font-size: 16px; }

.eh-section { display: flex; align-items: center; gap: 10px; margin: .4rem 0 .2rem; }
.eh-section .eh-ms { font-size: 22px; color: #2f6b4f; background: #e3eadb; border-radius: 10px; padding: 6px; }
.eh-section h3 { margin: 0 !important; padding: 0 !important; }

[data-testid="stMetricValue"] { font-family: 'Fraunces', Georgia, serif; }
[data-testid="stChatMessage"] { background: #fffdf8; border: 1px solid #e3e5d9; border-radius: 16px; padding: 14px 16px; }
[data-testid="stSidebarNav"] a span { font-weight: 500; }
@media (max-width: 640px) {
  .eh-hero { padding: 24px 20px; } .eh-hero .eh-title { font-size: 1.9rem; } .eh-title { font-size: 1.7rem; }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.logo(str(ASSETS / "logo.svg"), size="large", icon_image=str(ASSETS / "icon.svg"))


def _icon(name: str) -> str:
    return f'<span class="eh-ms">{escape(name)}</span>'


def page_header(icon: str, eyebrow: str, title: str, subtitle: str = "") -> None:
    """Icon tile + eyebrow + serif title. `icon` is a Material Symbols name, e.g. "forum"."""
    eyebrow, title, subtitle = t(eyebrow), t(title), t(subtitle) if subtitle else ""
    sub = f'<div class="eh-sub">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="eh-header"><div class="eh-icon">{_icon(icon)}</div><div>'
        f'<div class="eh-eyebrow">{escape(eyebrow)}</div><div class="eh-title">{escape(title)}</div>{sub}</div></div>',
        unsafe_allow_html=True,
    )


def hero(eyebrow: str, title: str, subtitle: str, chips: list[tuple[str, str]] = ()) -> None:
    """Large landing banner. `chips` are (icon, text) pairs."""
    eyebrow, title, subtitle = t(eyebrow), t(title), t(subtitle)
    chip_html = "".join(f'<span class="eh-chip">{_icon(i)}{escape(t)}</span>' for i, t in chips)
    chip_row = f'<div class="eh-chips">{chip_html}</div>' if chips else ""
    st.markdown(
        f'<div class="eh-hero"><span class="eh-ms eh-leaf">eco</span>'
        f'<div class="eh-eyebrow">{escape(eyebrow)}</div><div class="eh-title">{escape(title)}</div>'
        f'<div class="eh-sub">{escape(subtitle)}</div>{chip_row}</div>',
        unsafe_allow_html=True,
    )


def section(icon: str, title: str, caption: str = "") -> None:
    """Section heading with an icon badge."""
    st.markdown(f'<div class="eh-section">{_icon(icon)}<h3>{escape(t(title))}</h3></div>', unsafe_allow_html=True)
    if caption:
        st.caption(t(caption))


BOTANIST_SVG = """
<svg class="bt-figure" viewBox="0 0 120 150" width="104" height="130" role="img" aria-label="{alt}">
  <ellipse cx="60" cy="143" rx="30" ry="5" fill="#1f3d2e" opacity=".12"/>
  <!-- basket of herbs -->
  <g class="bt-basket">
    <path d="M14 112 q4 -14 14 -10 q-2 -12 8 -12 q6 0 6 10 q8 -4 10 6" fill="#4f8a63"/>
    <path d="M20 108 l2 -8 M30 104 l-2 -10 M40 106 l3 -9" stroke="#2f6b4f" stroke-width="2" stroke-linecap="round"/>
    <circle cx="26" cy="99" r="3" fill="#e9c46a"/><circle cx="38" cy="96" r="3" fill="#f2f2f2"/>
    <path d="M10 110 h44 l-5 22 h-34 z" fill="#b07a45"/>
    <path d="M12 117 h40 M14 124 h36" stroke="#8a5a2e" stroke-width="2"/>
  </g>
  <!-- body -->
  <g class="bt-body">
    <path d="M60 140 v-6 M74 140 v-6" stroke="#3b2f2a" stroke-width="6" stroke-linecap="round"/>
    <path d="M46 132 q0 -40 21 -40 q21 0 21 40 z" fill="#2f6b4f"/>
    <path d="M58 132 q0 -28 9 -36 q9 8 9 36 z" fill="#e8dcc0"/>
    <path d="M62 112 h10" stroke="#2f6b4f" stroke-width="2" stroke-linecap="round"/>
    <!-- arm holding basket -->
    <path d="M50 102 q-12 6 -10 14" stroke="#2f6b4f" stroke-width="7" stroke-linecap="round" fill="none"/>
    <circle cx="40" cy="116" r="4" fill="#e8b48c"/>
    <!-- waving arm with a leaf -->
    <g class="bt-wave">
      <path d="M84 102 q10 -8 12 -22" stroke="#2f6b4f" stroke-width="7" stroke-linecap="round" fill="none"/>
      <circle cx="96" cy="78" r="4.5" fill="#e8b48c"/>
      <g class="bt-leaf">
        <path d="M97 74 q4 -16 18 -18 q-2 16 -18 18 z" fill="#6aa84f"/>
        <path d="M97 74 l13 -13" stroke="#3f7a2f" stroke-width="1.2"/>
      </g>
    </g>
  </g>
  <!-- head -->
  <g class="bt-head">
    <circle cx="67" cy="76" r="14" fill="#e8b48c"/>
    <path d="M55 72 q2 -8 12 -8 q10 0 12 8" fill="#5a3b28"/>
    <g class="bt-eyes"><circle cx="62" cy="77" r="1.7" fill="#1f3328"/><circle cx="72" cy="77" r="1.7" fill="#1f3328"/></g>
    <path d="M62 83 q5 4 10 0" stroke="#7a3e2b" stroke-width="1.6" fill="none" stroke-linecap="round"/>
    <circle cx="58" cy="81" r="2" fill="#e38b7a" opacity=".5"/><circle cx="76" cy="81" r="2" fill="#e38b7a" opacity=".5"/>
    <!-- straw hat with a flower -->
    <ellipse cx="67" cy="64" rx="25" ry="5" fill="#d9b26f"/>
    <path d="M54 64 q1 -14 13 -14 q12 0 13 14 z" fill="#e6c27e"/>
    <path d="M54 61 h26" stroke="#2f6b4f" stroke-width="3"/>
    <circle cx="77" cy="58" r="3" fill="#f4f1e8"/><circle cx="77" cy="58" r="1.3" fill="#e9c46a"/>
  </g>
</svg>
"""

BOTANIST_CSS = """
<style>
.bt-wrap { display:flex; align-items:flex-end; gap:12px; margin:-.6rem 0 1.2rem; }
.bt-figure { flex-shrink:0; overflow:visible; }
.bt-bubble { position:relative; background:#fffdf8; border:1px solid #d9ddcf; border-radius:16px; padding:10px 14px;
  color:#1f3328; font-size:.95rem; line-height:1.45; max-width:520px; margin-bottom:34px;
  box-shadow:0 6px 16px rgba(31,61,46,.08); animation: bt-pop .5s ease-out both .3s; }
.bt-bubble:before { content:""; position:absolute; left:-8px; bottom:14px; width:14px; height:14px; background:#fffdf8;
  border-left:1px solid #d9ddcf; border-bottom:1px solid #d9ddcf; transform:rotate(45deg); }
.bt-body { animation: bt-breathe 3.2s ease-in-out infinite; transform-origin:67px 140px; }
.bt-head { animation: bt-nod 3.2s ease-in-out infinite; transform-origin:67px 90px; }
.bt-wave { animation: bt-wave 2.4s ease-in-out infinite; transform-origin:84px 102px; }
.bt-leaf { animation: bt-sway 2.4s ease-in-out infinite; transform-origin:97px 74px; }
.bt-eyes { animation: bt-blink 4.5s infinite; transform-origin:67px 77px; }
.bt-basket { animation: bt-breathe 3.2s ease-in-out infinite; transform-origin:32px 132px; }
@keyframes bt-wave { 0%,55%,100% { transform:rotate(0) } 12% { transform:rotate(-16deg) } 24% { transform:rotate(10deg) }
  36% { transform:rotate(-14deg) } 46% { transform:rotate(6deg) } }
@keyframes bt-sway { 0%,100% { transform:rotate(0) } 50% { transform:rotate(12deg) } }
@keyframes bt-nod { 0%,100% { transform:rotate(0) } 50% { transform:rotate(-4deg) } }
@keyframes bt-breathe { 0%,100% { transform:translateY(0) } 50% { transform:translateY(-1.5px) } }
@keyframes bt-blink { 0%,92%,100% { transform:scaleY(1) } 95% { transform:scaleY(.1) } }
@keyframes bt-pop { from { opacity:0; transform:translateY(6px) scale(.97) } to { opacity:1; transform:none } }
@media (prefers-reduced-motion: reduce) { .bt-wrap * { animation:none !important } }
@media (max-width:640px) { .bt-figure { width:78px; height:98px } .bt-bubble { font-size:.88rem } }
</style>
"""


def botanist(message: str, alt: str = "Animated botanist waving with a leaf") -> None:
    """Small animated herbalist (inline SVG + CSS, no JavaScript) with a speech bubble."""
    st.html(BOTANIST_CSS + f'<div class="bt-wrap">{BOTANIST_SVG.format(alt=escape(alt))}'
            f'<div class="bt-bubble">{escape(message)}</div></div>')
