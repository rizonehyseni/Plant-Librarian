"""Chat assistant that answers only from the fact sheets, with sources (proposal: "other ideas").

Retrieval is rule-based and runs on the local database: find the plants named in the
question (scientific, genus, or local/dialect name), build their fact sheets as numbered,
citable lines, and send only those lines to an LLM on Groq. The LLM writes the answer in the
user's language and must cite every claim, e.g. [R12]. Nothing outside the context is used.

Citation ids:  R<id> = traditional use record (study, page) · E<n> = manually reviewed study
               P<pmid> = PubMed candidate (unreviewed) · F<n> = safety/conservation flag
"""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

import requests
from rapidfuzz import fuzz

from .compare import compare_species, summary_sentence
from .config import GROQ_API_KEY, GROQ_MODEL, SEED
from .names import normalize, seed_names

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_PLANTS = 4              # plants with a full fact sheet per question
MAX_PUBMED_TITLES = 5       # unreviewed PubMed titles listed per plant
NAME_MATCH = 85             # fuzzy score for a dialect / misspelled name in the question
HISTORY_TURNS = 6           # earlier messages sent along for follow-up questions

SYSTEM_PROMPT = """You are the EthnoHack plant librarian, a research assistant for traditional \
medicinal-plant knowledge from Kosovo and the Albanian-speaking regions.

Rules:
1. Answer ONLY from the CONTEXT below. If the answer is not in the context, say that the \
project's data does not contain it. Never add facts from your own knowledge, not even \
well-known ones.
2. Cite every factual sentence with the ids in square brackets, e.g. [R12] or [E1][P31415926]. \
Use only ids that appear in the context.
3. Traditional use records are reports of what people said, not proof that a remedy works. \
PubMed candidates are unreviewed keyword matches; say so if you use them.
4. Never give doses, amounts, or treatment instructions, and never tell someone to take or \
stop a remedy or medicine. For health problems, suggest asking a doctor or pharmacist.
5. If no safety rule matched, do not call the plant safe: the safety list is limited.
6. If the question is not about plants, traditional plant use, or this project, politely say \
you can only help with the plant fact sheets.
7. Reply in the language of the user's question (Albanian or English). Keep scientific names \
in italics. Be concise; use short lists when they help."""


@dataclass
class Plant:
    species: str
    family: str | None = None
    local_names: set[str] = field(default_factory=set)
    uses: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Retrieval:
    context: str
    plants: list[str]
    sources: dict[str, dict[str, str]]  # citation id -> {label, url}


# --------------------------------------------------------------------------- data

def load_plants(conn) -> dict[str, Plant]:
    plants: dict[str, Plant] = {}
    rows = conn.execute(
        """SELECT uses.*, sources.title AS source_title, sources.url AS source_url
           FROM uses LEFT JOIN sources ON sources.doc_id = uses.doc_id
           WHERE uses.species IS NOT NULL AND uses.doc_id != 'sample_fixture'
           ORDER BY uses.id"""
    )
    for row in rows:
        r = dict(row)
        plant = plants.setdefault(r["species"], Plant(r["species"]))
        plant.family = plant.family or r.get("family")
        if r.get("local_name"):
            plant.local_names.add(r["local_name"])
        plant.uses.append(r)
    aliases = defaultdict(set)
    for alias, species in seed_names().items():
        aliases[species].add(alias)
    for species, names in aliases.items():
        if species in plants:
            plants[species].local_names |= names
    return plants


def load_reviewed() -> dict[str, list[dict[str, str]]]:
    path = SEED / "reviewed_evidence.csv"
    if not path.exists():
        return {}
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["species"]].append(row)
    return out


# --------------------------------------------------------------------------- retrieval

def _norm(name: str) -> str:
    # the PDF text has a dotless "ı" in some names (e.g. "Lule djellı"); NFKD does not fold it
    return normalize(name.replace("ı", "i"))


def _words(text: str) -> list[str]:
    return re.findall(r"[\w'-]+", text.replace("ı", "i").lower())


def _ngrams(text: str, max_n: int = 3) -> list[str]:
    words = _words(text)
    grams = []
    for n in range(1, max_n + 1):
        grams += [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]
    return grams


def _names_for(plant: Plant) -> set[str]:
    names = {_norm(plant.species)}
    genus = plant.species.split()[0]
    if len(genus) >= 4:
        names.add(_norm(genus))
    names |= {_norm(n) for n in plant.local_names}
    return {n for n in names if len(n) >= 3}


def find_plants(question: str, plants: dict[str, Plant]) -> list[str]:
    """Plants named in the question, best match first. Exact phrase beats fuzzy."""
    grams = {_norm(g) for g in _ngrams(question)}
    q_norm = " " + " ".join(_norm(w) for w in _words(question)) + " "
    scores: dict[str, float] = {}
    for species, plant in plants.items():
        best = 0.0
        for name in _names_for(plant):
            if f" {name} " in q_norm or name in grams:
                best = max(best, 100.0 + len(name))  # longer exact names rank higher
            elif len(name) >= 5:
                for g in grams:
                    if abs(len(g) - len(name)) <= 3:
                        best = max(best, fuzz.ratio(g, name))
        if best >= NAME_MATCH:
            scores[species] = best
    return sorted(scores, key=lambda s: -scores[s])[:MAX_PLANTS]


def _use_line(u: dict[str, Any]) -> str:
    place = u.get("place") or u.get("location") or "study area only"
    parts = [
        f"local name: {u.get('local_name') or '-'}",
        f"part: {u.get('part_used') or 'not stated'}",
        f"preparation: {u.get('preparation') or 'not stated'}",
        f"use: {u.get('use') or 'not stated'}",
        f"place: {place}",
        f"source: {u.get('source_title') or u.get('doc_id')}, page {u.get('page')}",
    ]
    return f"[R{u['id']}] " + "; ".join(parts)


def plant_sheet(conn, plant: Plant, reviewed: list[dict[str, str]], sources: dict, flag_counter: list[int]) -> str:
    sp = plant.species
    lines = [f"## Plant: {sp} (family: {plant.family or 'not listed'}; "
             f"local names: {', '.join(sorted(plant.local_names)) or 'none recorded'})"]

    lines.append("Traditional use records (what the study reports people do):")
    for u in plant.uses:
        lines.append("- " + _use_line(u))
        sources[f"R{u['id']}"] = {
            "label": f"{u.get('source_title') or u.get('doc_id')} · page {u.get('page')} · {sp}",
            "url": u.get("source_url") or "",
        }

    if reviewed:
        lines.append("Manually reviewed modern studies:")
        for row in reviewed:
            cid = f"E{len([k for k in sources if k.startswith('E')]) + 1}"
            lines.append(f"- [{cid}] {row['title']} ({row['year']}). Preparation tested: {row['preparation']}. "
                         f"Finding: {row['summary']} Comparison with the traditional preparation: "
                         f"{row['comparison']} Limitation: {row['limitation']}")
            sources[cid] = {"label": f"{row['title']} ({row['year']}) · reviewed", "url": row["url"]}
    else:
        lines.append("Manually reviewed modern studies: none yet for this plant.")

    papers = [dict(r) for r in conn.execute(
        "SELECT pmid, title, year, prep_class, study_type FROM evidence WHERE species = ? ORDER BY year DESC", (sp,))]
    # same-preparation check from PubMed tags only; the reviewed papers are listed above
    prep_check = compare_species(plant.uses, papers)
    lines.append(f"Was the same preparation tested? Automatic keyword check: {prep_check['label']}. "
                 f"{summary_sentence(prep_check)}")
    if papers:
        tags = Counter(p["prep_class"] for p in papers)
        kinds = Counter(p["study_type"] for p in papers)
        lines.append(
            f"PubMed candidates (UNREVIEWED keyword matches, tags can be wrong): {len(papers)} papers; "
            f"preparation tags: {dict(tags)}; study-type tags: {dict(kinds)}.")
        # same-preparation candidates first, they answer the user's most likely question
        listed = prep_check["matching_papers"] + [p for p in papers if p not in prep_check["matching_papers"]]
        for p in listed[:MAX_PUBMED_TITLES]:
            cid = f"P{p['pmid']}"
            lines.append(f"- [{cid}] {p['title']} ({p['year']}); tags: {p['prep_class']}, {p['study_type']}")
            sources[cid] = {"label": f"PubMed {p['pmid']}: {p['title']} · unreviewed",
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/"}
    else:
        lines.append("PubMed candidates: none loaded.")

    flags = [dict(r) for r in conn.execute("SELECT kind, level, note, source FROM flags WHERE species = ?", (sp,))]
    if flags:
        lines.append("Safety and conservation flags (from written rules and open databases):")
        for f in flags:
            flag_counter[0] += 1
            cid = f"F{flag_counter[0]}"
            lines.append(f"- [{cid}] {f['kind']} ({f['level']}): {f['note']}. Source: {f['source']}")
            url = f["source"] if str(f["source"]).startswith("http") else ""
            sources[cid] = {"label": f"{f['kind'].title()} ({f['level']}) · {sp}: {f['source']}", "url": url}
    else:
        lines.append("Safety flags: no rule in the project's LIMITED safety list matched (this is not an all-clear).")
    if not any(f["kind"] == "conservation" for f in flags):
        lines.append("Conservation status: not checked (IUCN lookup not available).")
    return "\n".join(lines)


def overview(conn, plants: dict[str, Plant], reviewed: dict[str, list], sources: dict) -> str:
    """Compact index of every record, used when the question names no plant (e.g. 'what helps a cough?')."""
    lines = ["## Safety and conservation flags for plants in the database"]
    flags = [dict(r) for r in conn.execute("SELECT species, kind, level, note, source FROM flags ORDER BY species")
             if r["species"] in plants]
    for n, f in enumerate(flags, 1):
        lines.append(f"[F{n}] {f['species']}: {f['kind']} ({f['level']}): {f['note']}. Source: {f['source']}")
        sources[f"F{n}"] = {"label": f"{f['kind'].title()} ({f['level']}) · {f['species']}: {f['source']}",
                            "url": f["source"] if str(f["source"]).startswith("http") else ""}
    lines.append("All other plants: no rule in the project's LIMITED safety list matched (not an all-clear).")
    lines.append("## Plants with manually reviewed modern studies: "
                 + (", ".join(sp for sp in sorted(reviewed) if sp in plants) or "none")
                 + ". Ask about one plant for details.")
    lines.append("## All traditional use records in the database (compact index)")
    for plant in sorted(plants.values(), key=lambda p: p.species):
        for u in plant.uses:
            lines.append(f"[R{u['id']}] {plant.species} ({u.get('local_name') or '-'}): "
                         f"{u.get('part_used') or '-'}; {u.get('preparation') or '-'}; {u.get('use') or '-'}")
            sources[f"R{u['id']}"] = {
                "label": f"{u.get('source_title') or u.get('doc_id')} · page {u.get('page')} · {plant.species}",
                "url": u.get("source_url") or "",
            }
    return "\n".join(lines)


def retrieve(conn, question: str, history: list[dict[str, str]] | None = None) -> Retrieval:
    plants = load_plants(conn)
    reviewed = load_reviewed()
    found = find_plants(question, plants)
    if not found:  # follow-up such as "is it safe?": reuse the plant from earlier user turns
        for msg in reversed(history or []):
            if msg["role"] == "user":
                found = find_plants(msg["content"], plants)
                if found:
                    break

    sources: dict[str, dict[str, str]] = {}
    study_rows = conn.execute("SELECT title, citation, url, licence FROM sources WHERE doc_id != 'sample_fixture'")
    header = ["# Project data",
              f"The database holds {sum(len(p.uses) for p in plants.values())} traditional use records "
              f"for {len(plants)} plants. Studies loaded:"]
    header += [f"- {r['title']}. {r['citation']}. {r['url']} (licence {r['licence']})" for r in study_rows]

    if found:
        flag_counter = [0]
        body = [plant_sheet(conn, plants[sp], reviewed.get(sp, []), sources, flag_counter) for sp in found]
    else:
        body = [overview(conn, plants, reviewed, sources)]
    return Retrieval(context="\n".join(header) + "\n\n" + "\n\n".join(body), plants=found, sources=sources)


# --------------------------------------------------------------------------- LLM

def build_messages(question: str, retrieval: Retrieval, history: list[dict[str, str]] | None = None) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nCONTEXT:\n" + retrieval.context}]
    for msg in (history or [])[-HISTORY_TURNS:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})
    return messages


def ask_groq(messages: list[dict], api_key: str = GROQ_API_KEY, model: str = GROQ_MODEL) -> str:
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env (free key: https://console.groq.com/keys).")
    r = requests.post(
        GROQ_URL, timeout=60,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "messages": messages, "temperature": 0.1, "max_tokens": 900},
    )
    if r.status_code == 429:
        raise RuntimeError("Groq rate limit reached. Wait a minute and ask again.")
    if not r.ok:
        raise RuntimeError(f"Groq API error {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"]


def cited_ids(answer: str, sources: dict[str, Any]) -> list[str]:
    """Citation ids the answer used, in order, keeping only ids that exist in the context."""
    seen: list[str] = []
    for group in re.findall(r"\[([^\]]+)\]", answer):  # [R1] and also [R1, R2]
        for cid in re.findall(r"\b[REPF]\d+\b", group):
            if cid in sources and cid not in seen:
                seen.append(cid)
    return seen


def answer(conn, question: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    retrieval = retrieve(conn, question, history)
    text = ask_groq(build_messages(question, retrieval, history))
    ids = cited_ids(text, retrieval.sources)
    return {"answer": text, "plants": retrieval.plants,
            "citations": [{"id": i, **retrieval.sources[i]} for i in ids]}
