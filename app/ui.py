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
