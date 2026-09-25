#!/usr/bin/env python3
"""Build README.md from the files in data/.

Usage:  python3 scripts/build_readme.py

Every table, count and badge in README.md is generated from data/*.csv and
data/*.json. To update the list, edit the data files (or add rows) and rerun
this script. It uses the Python standard library only.
"""
import csv
import json
import os
import re
import sys
from collections import Counter, OrderedDict
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


# ----------------------------------------------------------------------------- helpers
def rows(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def esc(text):
    """Escape characters that would break a Markdown table cell; em dashes in quoted text become commas."""
    text = (text or "").replace(" — ", ", ").replace("—", ", ")
    return text.replace("|", "&#124;").replace("\n", " ").strip()


def badge(label, message, color, style="flat-square"):
    q = lambda s: quote(s.replace("-", "--").replace("_", "__"), safe="")
    return f"https://img.shields.io/badge/{q(label)}-{q(message)}-{color}.svg?style={style}"


def img(label, message, color, alt=None):
    return f'<img src="{badge(label, message, color)}" alt="{alt or message}"/>'


def anchor(heading):
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- \ufe0f]", "", s, flags=re.UNICODE)  # GitHub keeps the emoji variation selector
    return s.replace(" ", "-")


def shorten(text, n):
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + " …"


VENUES = [
    (r"Advances in Neural Information Processing Systems|NeurIPS|Neural Information Processing", "NeurIPS"),
    (r"International Conference on Machine Learning|^ICML|Proceedings of Machine Learning Research", "ICML / PMLR"),
    (r"International Conference on Learning Representations", "ICLR"),
    (r"Findings of the Association for Computational Linguistics", "Findings of ACL"),
    (r"Empirical Methods in Natural Language Processing", "EMNLP"),
    (r"North American Chapter", "NAACL"),
    (r"European Chapter", "EACL"),
    (r"Annual Meeting of the Association for Computational Linguistics|Proceedings of the \d+(st|nd|rd|th) Annual Meeting", "ACL"),
    (r"Transactions of the Association for Computational Linguistics", "TACL"),
    (r"AAAI", "AAAI"),
    (r"Knowledge Discovery and Data Mining|KDD", "KDD"),
    (r"Uncertainty in Artificial Intelligence", "UAI"),
    (r"Artificial Intelligence and Statistics", "AISTATS"),
    (r"Journal of Machine Learning Research", "JMLR"),
    (r"Transactions on Machine Learning Research", "TMLR"),
    (r"Computer Vision and Pattern Recognition", "CVPR"),
    (r"International Joint Conference on Artificial Intelligence", "IJCAI"),
    (r"Fairness, Accountability, and Transparency", "FAccT"),
    (r"Conference on Language Modeling", "COLM"),
]


def venue(v):
    for pat, short in VENUES:
        if re.search(pat, v or ""):
            return short
    return shorten(v, 48)


def md_table(header, body, align=None):
    align = align or ["---"] * len(header)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(out)


def details(summary, body, open_=False):
    return f"<details{' open' if open_ else ''}>\n<summary>{summary}</summary>\n\n{body}\n\n</details>"


# ----------------------------------------------------------------------------- data
meta = load("meta.json")
papers = rows("papers.csv")
studies = rows("studies.csv")
fams = rows("families.csv")
t1 = rows("census_t1.csv")
dsets = rows("datasets.csv")
dcensus = rows("census_datasets.csv")
tools = rows("tooling.csv")
web = rows("web_sources.csv")
facts = rows("hosted_facts.csv")
atlas = rows("atlas.csv")
asrc = rows("atlas_sources.csv")
patterns = rows("patterns.csv")
checklist = rows("checklist.csv")
parents = rows("derivative_parents.csv")
related = rows("related_lists.csv")
counts = {r["key"]: r["value"] for r in rows("census_counts.csv")}
ev = load("evidence_counts.json")
HEADS = meta["heads"]
REPO = meta["repo"]

# ----------------------------------------------------------------------------- consistency checks
# The v1.0 census and ledger are frozen; the data files may grow after the cutoff but never shrink below them.
rob_n = Counter(s["rob_overall"] or "pending" for s in studies)
ledger_rows = sum(int(s["rows"] or 0) for s in studies)
checks = [
    ("open original implementations (T1)", len(t1), int(counts["hf.t1Count"])),
    ("census datasets (D)", len(dcensus), int(counts["hf.dCount"])),
    ("graded studies", len(studies) - rob_n["pending"], int(ev["rob.studiesGraded"])),
    ("ledger rows", ledger_rows, int(ev["ledger.rows"])),
    ("failure modes", len(atlas), 15),
    ("design patterns", len(patterns), 13),
]
bad = [c for c in checks if c[1] < c[2]]
if bad:
    sys.exit("Count below the v1.0 release: " + "; ".join(f"{n} {a} < {b}" for n, a, b in bad))

stream_codes = [s["code"] for s in meta["streams"]]
genealogy = [p for p in papers if p["group"] in stream_codes]
dataset_ids = {d["id"] for d in dcensus} | {d["id"] for d in dsets}
hosted_n = 1
github_only = [f for f in fams if not f["hf"]]
n_papers = len(papers)
n_models = hosted_n + len(t1) + len(github_only)
n_resources = n_papers + len(studies) + n_models + len(dataset_ids) + len(tools) + len(web) + len(related)

# ----------------------------------------------------------------------------- pieces
def paper_row(p):
    mark = " 📖" if p["in_survey"] == "yes" else ""
    return [p["year"], f"[{esc(p['title'])}]({p['link']}){mark}", esc(p["first_author"]), esc(venue(p["venue"]))]


def head_badge(code):
    if not code:
        return "not classified"
    h = HEADS[code]
    return img("head", h["name"], h["color"], h["name"])


ROB = {"low": ("low", "brightgreen"), "some_concerns": ("some concerns", "yellow"), "high": ("high", "red"),
       "": ("pending", "lightgrey")}


def rob_badge(level):
    text, color = ROB[level]
    return img("risk of bias", text, color, f"risk of bias: {text}")


def hf(id_):
    return f"https://huggingface.co/{id_}"


def study_link(key):
    s = next((x for x in studies if x["key"] == key), None)
    if s is None:
        return key
    label = s["authors"] + " (" + s["date"][:4] + ")" if s["source"] == "arXiv" else s["title"]
    return f"[{esc(label)}]({s['link']})"


def evidence_link(ref):
    if ref.startswith("card:"):
        i = ref[5:]
        return f"[{i}]({hf(i)})"
    if ref.startswith("doc:"):
        u = ref[4:]
        return f"[TypeSafe docs]({u})"
    return study_link(ref)


out = []
A = out.append

# ============================================================================= header
A('<div align="center">\n')
A("# 🧭 Awesome System One Models")
A("### *Typed probabilistic decision models: a curated, evidence-graded map of the contract, the models and the failures*\n")
A('<p align="center">\n  <img src="fig/contract.png" width="820" alt="The decision contract: a state and a typed question pass through a decision head in one forward pass to a distribution over the options, which a policy threshold turns into act, review or escalate"/>\n</p>\n')
badges = [
    ("[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)"),
    ("[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)"),
    (f"[![GitHub stars](https://img.shields.io/github/stars/{REPO}.svg?style=social&label=Star)](https://github.com/{REPO})"),
    ("[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)"),
    (f"[![Last Updated]({badge('Last Updated', meta['last_updated_badge'], 'blue')})](https://github.com/{REPO}/commits/main)"),
    (f"[![Resources]({badge('Resources', str(n_resources), 'orange')})](#-at-a-glance)"),
    (f"[![Version]({badge('version', 'v' + meta['version'] + ' · cutoff ' + meta['cutoff'], '6c3483')})](#-cutoff-and-versioning)"),
]
A("\n".join(badges) + "\n")
A("</div>\n\n---\n")
A('<div align="center">\n')
A(f"Maintained alongside &nbsp;<strong>{meta['survey']['title']}</strong> &nbsp;·&nbsp; Rafe and Das, <em>{meta['survey']['status']}</em> &nbsp; "
  f"<img src=\"{badge('survey', 'under review', '1d4776')}\" alt=\"survey under review\"/>\n")
A("</div>\n\n---\n")
A('<div align="center">\n')
A('### 🎯 *"A decision model is a new contract, not a new kind of intelligence."*\n')
A(f"**{n_papers} registry-verified papers · {len(studies)} graded studies · {n_models} models · {len(dataset_ids)} datasets · {len(tools)} tools**  ")
A("*Organized by the survey's own structure: genealogy, anatomy, census, evidence, failures, patterns and reporting*\n")
quick = [("🧩 Concept", "🧩 What is a System One model?"), ("🌳 Genealogy", "🌳 Genealogy"), ("🤖 Models", "🤖 Models"),
         ("🔬 Evidence", "🔬 Evidence"), ("🧨 Failure atlas", "🧨 Failure atlas"), ("🧱 Patterns", "🧱 Design patterns")]
A(" • ".join(f"[{t}](#{anchor(h)})" for t, h in quick) + " • [🤝 Contribute](CONTRIBUTING.md) • [📝 Cite](#-how-to-cite)\n")
A("</div>\n\n---\n")

# ============================================================================= contents
toc = ["🧩 What is a System One model?", "🚀 Quick Start", "📊 At a glance", "🗺️ Taxonomy", "🌳 Genealogy", "🤖 Models",
       "📚 Datasets and benchmarks", "🛠️ Harnesses and tooling", "🔬 Evidence", "🧨 Failure atlas", "🧱 Design patterns",
       "✅ Reporting checklist in brief", "📖 Surveys and related resources", "🤝 Contributing", "📝 How to cite",
       "🕒 Cutoff and versioning", "📜 License", "👥 Authors and maintainers"]
A("## 📌 Contents\n")
half = (len(toc) + 1) // 2
A("<table><tr><td valign=\"top\">\n\n" + "\n".join(f"{i+1}. [{h}](#{anchor(h)})" for i, h in enumerate(toc[:half])) +
  "\n\n</td><td valign=\"top\">\n\n" + "\n".join(f"{i+1+half}. [{h}](#{anchor(h)})" for i, h in enumerate(toc[half:])) +
  "\n\n</td></tr></table>\n")

# ============================================================================= concept
A("## 🧩 What is a System One model?\n")
A("A System One model, also called a typed probabilistic decision model, maps a state and a caller-declared typed question "
  "to a probability distribution over a finite answer space, in one forward pass and without generating text. The question "
  "is one of three primitives, **Choice** over named options, **Score** over ordered levels, or **Noul** for a yes-or-no "
  "judgment, and the model promises that the returned probabilities are calibrated. The survey reads this as a new contract "
  "assembled from five older research lines rather than as a new kind of intelligence, so the unit of evaluation is the "
  "contract together with the policy that consumes the probability and chooses to act, review or escalate. The versioned "
  "artifacts drawn along the bottom of the figure above (model revision, serving temperature, option texts and rubric) belong "
  "to the contract, because a change in any of them yields a different predictor.\n")
A(md_table(["Primitive", "Answer space", "Returned", "Confidence value"],
           [["**Choice**", "Declared options (up to 255 on the hosted model)", "Distribution over the options", "Yes"],
            ["**Score**", "Ordered levels (2 to 10 on the hosted model)", "Distribution over the levels", "Yes"],
            ["**Noul**", "Yes or no", "Probability of yes", "Not returned by the hosted model"]]) + "\n")

# ============================================================================= quick start
A("## 🚀 Quick Start\n")
A("""```mermaid
graph TD
    A[🎯 Need a typed decision from text or JSON state?] --> B{Hosted API or open weights?}
    B -->|Hosted| C[☁️ Jev 1.13 through the vendor API]
    B -->|Open weights| D[🔓 Pick an open family by head, size and license]
    C --> E[🧨 Check the failure atlas for your task]
    D --> E
    E --> F[🧪 Audit calibration on your own schema]
    F --> G[🧱 Apply a pattern: gate, cascade or review budget]
    G --> H[✅ Report with the checklist]
    H --> I[🔬 Compare with the graded evidence]
```
""")

# ============================================================================= stats
A("## 📊 At a glance\n")
gc = Counter(p["group"] for p in genealogy)
tc = Counter(t["category"] for t in tools)
stat_lines = [
    f"- **📄 Registry-verified papers**: {n_papers}, of which {len(genealogy)} sit in the five genealogy streams "
    + ", ".join(f"{s['code']} {gc[s['code']]}" for s in meta["streams"]),
    f"- **☁️ Hosted decision models**: {hosted_n} (Jev 1.13, TypeSafe AI)",
    f"- **🔓 Open original implementations on Hugging Face (T1)**: " + (f"{len(t1)} checkpoints in {counts['hf.t1Families']} families, " if len(t1) == int(counts['hf.t1Count'])
         else f"{len(t1)} checkpoints ({counts['hf.t1Count']} in {counts['hf.t1Families']} families at the v1.0 cutoff), ")
    + f"{counts['hf.t1.distinctBackboneFamilies']} backbone families, first releases {counts['hf.t1.releaseDateSpan']}",
    f"- **🧬 Derivatives (T2)**: {counts['hf.t2Count']} (format conversions {counts['hf.t2.formatConversion']}, quantizations {counts['hf.t2.quantization']}, "
    f"language fine-tunes {counts['hf.t2.finetuneLanguage']}, domain fine-tunes {counts['hf.t2.finetuneDomain']}, merges {counts['hf.t2.merge']}, other {counts['hf.t2.other']})",
    f"- **📚 Datasets**: {len(dcensus)} typed-decision datasets on Hugging Face, {len(dsets)} with a full card",
    f"- **🐙 GitHub repositories screened**: {counts['gh.countTotal']} (local servers {counts['gh.countLocalServer']}, integrations {counts['gh.countIntegration']}, "
    f"applications {counts['gh.countApplication']}, open-model training {counts['gh.countOpenModelTraining']}, evaluation {counts['gh.countEvaluation']})",
    f"- **🔬 Evidence ledger**: {ledger_rows} extracted values from {len(studies)} studies; risk of bias low {rob_n['low']}, "
    f"some concerns {rob_n['some_concerns']}, high {rob_n['high']}" + (f", pending {rob_n['pending']}" if rob_n['pending'] else ""),
    f"- **🧨 Failure modes**: {len(atlas)} · **🧱 Design patterns**: {len(patterns)} · **✅ Checklist items**: {len(checklist)} in 5 groups",
    f"- **🕒 Cutoff**: {meta['cutoff']} (v{meta['version']})",
]
A(details("📊 <strong>Repository statistics</strong> (click to expand)", "\n".join(stat_lines)) + "\n")

# ============================================================================= taxonomy
A("## 🗺️ Taxonomy\n")
A("The list follows the survey's conceptual structure. A decision model is described by its contract, its head and its "
  "objective. It is placed in the ecosystem by the census, judged by the graded evidence, and deployed through patterns that "
  "answer documented failure modes.\n")
A("""```mermaid
mindmap
  root((System One models))
    Contract
      Choice
      Score
      Noul
      Versioned artifacts
    Heads
      Fixed slots
      Option markers
      Label logits
      Pair scoring
      Constrained decoding
    Objectives
      Cross-entropy on options
      Proper scores and RLCD
      Post-hoc temperature
    Policy
      Gate
      Cascade and escalation
      Review budget
    Evidence
      Risk of bias
      Three regularities
      Failure atlas
```
""")

# ============================================================================= genealogy
A("## 🌳 Genealogy\n")
A("The decision contract is best read as a convergence of five older research lines rather than as an invention of "
  "September 2026. The timeline places each stream on its own lane; the right panel shows the open implementations that "
  "followed the hosted release within days. Papers marked 📖 are discussed in the survey; the others come "
  "from the same registry-verified bibliography.\n")
A('<p align="center"><img src="fig/timeline.png" width="860" alt="Timeline of the five research streams converging on Jev 1.13 on 15 September 2026, followed by open implementations"/></p>\n')
A(md_table(["Stream", "Contributes", "Papers"],
           [[f"{s['emoji']} [{s['name']}](#{anchor(s['emoji'] + ' ' + s['code'] + ' ' + s['name'])})", s["gives"], str(gc[s["code"]])]
            for s in meta["streams"]]) + "\n")
for s in meta["streams"]:
    ps = sorted([p for p in genealogy if p["group"] == s["code"]], key=lambda p: (p["year"], p["title"]))
    A(f"### {s['emoji']} {s['code']} {s['name']}\n")
    A(f"> {s['summary']}\n")
    body = md_table(["Year", "Title", "First author", "Venue"], [paper_row(p) for p in ps], ["---:", "---", "---", "---"])
    A(details(f"<strong>{len(ps)} papers</strong>, {sum(p['in_survey'] == 'yes' for p in ps)} discussed in the survey", body) + "\n")

# ============================================================================= models
A("## 🤖 Models\n")
A("### ☁️ Hosted model\n")
A("**Jev 1.13** from TypeSafe AI launched on 15 September 2026 with the post that introduced the System One name. "
  "Its weights, architecture and RLCD training recipe are not published, so statements about its internals rest on the "
  "vendor's own descriptions or on black-box probing. The facts below are the vendor's, as documented on the access date.\n")
A(md_table(["Fact", "Value", "Source"], [[esc(f["fact"]), esc(f["value"]), f"[link]({f['source']})"] for f in facts]) + "\n")
vdocs = [w_ for w_ in web if w_["kind"] == "vendor documentation"]
A(details(f"📘 <strong>Vendor documentation and access points</strong> ({len(vdocs)} pages)",
          md_table(["Page", "Publisher", "Page date", "Accessed"],
                   [[f"[{esc(d['title'])}]({d['url']})", esc(d["publisher"]), esc(d["page_date"]), d["accessed"]] for d in vdocs])) + "\n")
sdk = [t for t in tools if t["category"] in ("vendor_sdk",)]
A("The official SDKs are " + ", ".join(f"[{t['name']}]({t['repo']})" for t in sdk[:-1])
  + f" and [{sdk[-1]['name']}]({sdk[-1]['repo']}).\n")

A("### 🔓 Open original implementations\n")
A("Open label-conditioned heads on public backbones reproduced the typed contract within days of the hosted release. "
  "The table condenses the notable families with an independent card; each head badge follows the survey's five-way head "
  "taxonomy, assigned from the card's own description of its decision head.\n")
A('<p align="center"><img src="fig/heads.png" width="860" alt="Five decision-head archetypes: fixed slots, option markers, label logits, pair scoring and constrained decoding, with the census families under each"/></p>\n')
A("<p align=\"center\">" + " ".join(img("head", HEADS[k]["name"], HEADS[k]["color"]) for k in "abcde") + "</p>\n")
fam_rows = []
for f in fams:
    links = []
    for i in [x for x in f["hf"].split(";") if x]:
        links.append(f"[🤗 {i.split('/')[-1]}]({hf(i)})")
    if f["code"]:
        links.append(f"[code]({f['code']})")
    fam_rows.append([f"**{esc(f['family'])}**", esc(f["author"]), f["first_release"], esc(f["backbone"]), esc(f["params"]),
                     head_badge(f["head"]), esc(f["license"]), "<br>".join(links)])
A(md_table(["Family", "Author", "First release", "Backbone", "Size", "Head", "License", "Links"], fam_rows) + "\n")
A(details("🌡️ <strong>Calibration as shipped, per family</strong>",
          md_table(["Family", "Head as described", "Primitives", "Temperature or calibration as shipped"],
                   [[esc(f["family"]), esc(f["head_text"]), esc(f["primitives"]), esc(f["calibration"])] for f in fams])) + "\n")

t1_rows = [[f"[{esc(t['id'])}]({hf(t['id'])})", t["created"], esc(t["base_model"]) or "not stated", t["params"] or "n/a",
            esc(t["license"]), head_badge(t["head"]) if t["head"] else "·"] for t in t1]
A(details(f"🧾 <strong>Full census of open original implementations</strong> ({len(t1)} Hugging Face checkpoints, tier T1)",
          "Head badges appear only where a full census card describes the decision head; other rows are not classified.\n\n" +
          md_table(["Checkpoint", "Created", "Base model", "Params", "License", "Head"], t1_rows)) + "\n")
A(details(f"🧬 <strong>Derivatives</strong> ({counts['hf.t2Count']} tier-T2 repositories)",
          md_table(["Kind", "Count"], [["Format conversions (GGUF, ONNX, MLX and similar)", counts["hf.t2.formatConversion"]],
                                         ["Quantizations", counts["hf.t2.quantization"]],
                                         ["Language fine-tunes", counts["hf.t2.finetuneLanguage"]],
                                         ["Domain fine-tunes", counts["hf.t2.finetuneDomain"]],
                                         ["Merges", counts["hf.t2.merge"]], ["Other", counts["hf.t2.other"]]]) +
          "\n\nMost-derived parents:\n\n" +
          md_table(["Parent", "Derivatives"], [[f"[{p['parent']}]({p['url']})" if p["url"] else f"{p['parent']} (gated or removed)", p["derivatives"]]
                                                for p in parents])) + "\n")

# ============================================================================= datasets
A("## 📚 Datasets and benchmarks\n")
A("Typed-decision datasets appeared alongside the models. Label construction differs sharply between them, from human gold "
  "labels to teacher-model labels and synthetic generation, so reference-label provenance should be read before any number.\n")
A(md_table(["Dataset", "Author", "License", "Purpose (from the card)"],
           [[f"[{d['id']}](https://huggingface.co/datasets/{d['id']})", esc(d["author"]), esc(d["license"]), esc(shorten(d["purpose"], 220))]
            for d in dsets]) + "\n")
A(details(f"🗃️ <strong>All typed-decision datasets in the census</strong> ({len(dcensus)})",
          md_table(["Dataset", "Created", "License"],
                   [[f"[{d['id']}](https://huggingface.co/datasets/{d['id']})", d["created"], esc(d["license"])] for d in dcensus])) + "\n")
dp = [p for p in papers if p["group"] == "DATA"]
A("**Public benchmarks reused in the evidence**\n")
A(md_table(["Year", "Title", "First author", "Venue"], [paper_row(p) for p in sorted(dp, key=lambda p: p["year"])],
           ["---:", "---", "---", "---"]) + "\n")
A("The vendor also publishes [workflow evals](https://evals.typesafe.ai/), graded in the ledger as a developer evaluation "
  "whose reference is a model consensus.\n")

# ============================================================================= tooling
A("## 🛠️ Harnesses and tooling\n")
A("Each entry has a census card with a pinned commit. Stars are as recorded on the census date. Plug-ins for coding "
  "assistants are counted in the census but not listed individually.\n")
CATS = OrderedDict([("vendor_sdk", "📦 Vendor SDKs"), ("vendor_cookbook", "📒 Vendor cookbooks"),
                    ("local_server", "🖥️ Local servers and runtimes"), ("integration", "🔌 Integrations"),
                    ("evaluation", "📏 Evaluation packages and benchmarks"),
                    ("open_model_training", "🏗️ Open-model training code")])


def star_key(t):
    try:
        return -int(t["stars"])
    except ValueError:
        return 1


for cat, label in CATS.items():
    ts = sorted([t for t in tools if t["category"] == cat], key=lambda t: (star_key(t), t["name"].lower()))
    if not ts:
        continue
    body = md_table(["Repository", "⭐", "License", "Created", "What it does"],
                    [[f"[{esc(t['name'])}]({t['repo']})", t["stars"] or "·", esc(t["license"]) or "·", t["created"],
                      esc(shorten(t["description"], 180))] for t in ts], ["---", "---:", "---", "---", "---"])
    A(details(f"{label} <strong>({len(ts)})</strong>", body, open_=(cat == "vendor_sdk")) + "\n")

# ============================================================================= evidence
A("## 🔬 Evidence\n")
A("The evidence ledger holds one row per study, model, task and metric, each with a verbatim excerpt and location in the "
  "primary source. Every study is graded on five risk-of-bias domains adapted from PROBAST and QUADAS-AI (reference-label "
  "independence, sampling, version pinning, tuning-budget parity and test-set exposure). The badge shows the overall grade.\n")
A("> [!IMPORTANT]\n> **Three regularities from the graded evidence**\n>\n" +
  "\n".join(f"> **{r['id']} · {r['name']}.** {r['short']}  " for r in meta["regularities"]) + "\n")
A("<p align=\"center\">" + " ".join([img("risk of bias", f"low · {rob_n['low']}", "brightgreen"),
                                      img("risk of bias", f"some concerns · {rob_n['some_concerns']}", "yellow"),
                                      img("risk of bias", f"high · {rob_n['high']}", "red")]) + "</p>\n")
srows = []
for i, s in enumerate(studies, 1):
    own = " †" if s["own"] == "yes" else ""
    title = f"[{esc(s['title'])}]({s['link']}){own}<br><sub>{esc(s['authors'])} · {s['date']} · {esc(s['role'])}</sub>"
    srows.append([str(i), title, esc(s["task_family"]),
                  f"{esc(s['decision_models'])}<br><sub>vs. {esc(s['comparators'])}</sub>", esc(s["reference_labels"]),
                  rob_badge(s["rob_overall"])])
A(md_table(["#", "Study", "Task family", "Decision models", "Reference labels", "Grade"], srows,
           ["---:", "---", "---", "---", "---", "---"]) + "\n")
A("<sub>† The authors' own study. Grey-literature entries (cards, repositories, posts) are graded like papers. A grade "
  "describes the evidence behind a study's numbers, not the quality of the models it tests.</sub>\n")

# ============================================================================= atlas
A("## 🧨 Failure atlas\n")
A("Fifteen failure modes crossed with the hosted model, the open families of the companion benchmark and a pooled "
  "generative comparator. A ✓ records that evidence on the failure mode exists for that model, not that the failure was "
  "observed; several measured cells are favorable. Superscripts give the source: <sup>V</sup> documented by the vendor or "
  "developer, <sup>L</sup> measured in a ledger study, <sup>B</sup> measured in the authors' companion benchmark "
  "(manuscript in preparation).\n")
MOD = [("jev", "Jev 1.13"), ("laya", "Laya"), ("kev", "Kev"), ("nimble", "Nimble"), ("thisthat", "this-that"),
       ("decider", "decider"), ("comparator", "Generative comparator")]


def cell(v):
    if not v:
        return "·"
    return "✓<sup>" + ",".join(v.split(";")) + "</sup>"


arows, last = [], None
for r in atlas:
    if r["group"] != last:
        arows.append([f"***{r['group']}***"] + [""] * len(MOD))
        last = r["group"]
    arows.append([f"{r['row']}. {r['failure_mode']}"] + [cell(r[m]) for m, _ in MOD])
A(md_table(["Failure mode", "☁️ " + MOD[0][1]] + [n for _, n in MOD[1:6]] + ["🧠 " + MOD[6][1]], arows,
           ["---"] + [":---:"] * len(MOD)) + "\n")
src_lines = []
for r in atlas:
    items = [s for s in asrc if s["row"] == r["row"]]
    if not items:
        continue
    names = dict(MOD)
    parts = OrderedDict()
    for s in items:
        parts.setdefault(names[s["model"]], []).append(f"[{esc(s['label'])}]({s['url']})<sup>{s['code']}</sup>")
    src_lines.append(f"- **{r['row']}. {r['failure_mode']}**: " + "; ".join(f"{m} ({', '.join(v)})" for m, v in parts.items()))
A(details("🔎 <strong>Sources behind each vendor and ledger mark</strong>",
          "\n".join(src_lines) + "\n\nBenchmark marks come from the companion benchmark and are not linked until it is public.") + "\n")

# ============================================================================= patterns
A("## 🧱 Design patterns\n")
A("A pattern is a recurring way of composing decision-model calls with ordinary code, and each one consumes a probability "
  "quantity whose meaning the survey fixes formally. The guarantee is 🟢 proved under the calibration its proposition "
  "assumes, 🟡 empirical or conformal, or ⚪ none. Rows refer to the failure atlas above.\n")
G = {"full": "🟢", "half": "🟡", "none": "⚪"}
prow, last = [], None
for p in patterns:
    if p["role"] != last:
        prow.append([f"***{p['role']}***", "", "", "", ""])
        last = p["role"]
    ev_links = ", ".join(evidence_link(e) for e in p["evidence"].split(";") if e)
    prow.append([f"**{p['pattern']}**", esc(p["quantity"]), f"{G[p['guarantee']]} {esc(p['guarantee_text'])}",
                 ", ".join(p["atlas_rows"].split(";")) or "·", ev_links])
A(md_table(["Pattern", "Quantity consumed", "Guarantee", "Atlas rows", "Evidence"], prow) + "\n")

# ============================================================================= checklist
A("## ✅ Reporting checklist in brief\n")
A("Pin the model and its revision, the serving temperature, the schema with its option identifiers and rubrics, the state "
  "encoding, and the access dates of every hosted service. Sample with the provenance of the reference labels stated, "
  "together with the sample size and any exposure of the test items in public data. Report the calibration quantity that "
  "fits each primitive, state a cascade result as retained quality against a cost fraction under one cost definition, and "
  "treat a changed revision as a new predictor.\n")
groups = OrderedDict()
for c in checklist:
    groups.setdefault(c["group"], []).append(c)
GE = {"What to pin": "📌", "What to sample": "🎲", "Calibration quantity per primitive": "🌡️",
      "Cascade and review results": "🔀", "Handling version churn": "🔁"}
A(md_table(["Group", "Items"], [[f"{GE.get(g, '')} **{g}**", ", ".join(i["item"] for i in items)] for g, items in groups.items()]) + "\n")
A(details("📋 <strong>What to report for each item</strong>",
          md_table(["Group", "Item", "What to report"], [[esc(c["group"]), f"**{esc(c['item'])}**", esc(c["report"])] for c in checklist])) + "\n")

# ============================================================================= related
A("## 📖 Surveys and related resources\n")
sv = sorted([p for p in papers if p["survey_paper"] == "yes"], key=lambda p: (p["year"], p["title"]))
A("### 📑 Surveys and reviews of neighboring lines\n")
A(md_table(["Year", "Title", "First author", "Venue"], [paper_row(p) for p in sv], ["---:", "---", "---", "---"]) + "\n")
for code, label, blurb in [
    ("RPT", "🧾 Reporting and appraisal standards", "Precedents for the checklist and the risk-of-bias domains."),
    ("ADJ", "🔧 Adjacent lines", "Constrained decoding, structured output, tool use and serving. These obtain a valid type from a sampled sequence and are the natural comparator rather than an ancestor."),
    ("STATS", "📐 Statistics for evaluation", "Tests, intervals and rank correlations used when comparing decision models."),
]:
    ps = sorted([p for p in papers if p["group"] == code], key=lambda p: (p["year"], p["title"]))
    A(details(f"{label} <strong>({len(ps)})</strong>", blurb + "\n\n" +
              md_table(["Year", "Title", "First author", "Venue"], [paper_row(p) for p in ps], ["---:", "---", "---", "---"])) + "\n")
com = [w_ for w_ in web if w_["kind"] in ("commentary", "discussion", "vendor or partner post")]
A("### 🗞️ Commentary, launch coverage and other lists\n")
A(md_table(["Resource", "Publisher", "Date", "Kind"],
           [[f"[{esc(c['title'])}]({c['url']})", esc(c["publisher"]), esc(c["page_date"]), c["kind"]] for c in com] +
           [[f"[{r['name']}]({r['url']})", r["name"].split("/")[0], "·", f"curated list, {r['stars']} ⭐ at census"] for r in related]) + "\n")

# ============================================================================= contributing
A("## 🤝 Contributing\n")
A('<div align="center">\n')
A("<table><tr>\n<td align=\"center\" width=\"33%\">\n\n**📄 Add a paper**<br>Measured a decision model?<br>"
  "[Open a paper issue](https://github.com/pozapas/awesome-system-one-models/issues/new?template=add-paper.yml)\n\n</td>\n<td align=\"center\" width=\"33%\">\n\n"
  "**🤖 Add a model or dataset**<br>Released a checkpoint or corpus?<br>[Open a model issue](https://github.com/pozapas/awesome-system-one-models/issues/new?template=add-model.yml)\n\n"
  "</td>\n<td align=\"center\" width=\"33%\">\n\n**🩹 Report a correction**<br>Found a wrong value or dead link?<br>"
  "[Open a correction](https://github.com/pozapas/awesome-system-one-models/issues/new?template=correction.yml)\n\n</td>\n</tr></table>\n")
A("[![Contribute Now](https://img.shields.io/badge/Contribute-Read%20the%20guide-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)\n")
A("</div>\n")
A("Additions follow the survey's inclusion rules. A study enters the evidence table when it reports a measured quantity "
  "for a typed probabilistic decision model on a stated task against a stated reference. Tables are generated, so a pull "
  "request edits the files in [`data/`](data/) and reruns `python3 scripts/build_readme.py`. See [CONTRIBUTING.md](CONTRIBUTING.md).\n")

# ============================================================================= cite
A("## 📝 How to cite\n")
A("If this list helps your work, please cite the survey it accompanies.\n")
A("```bibtex\n@unpublished{rafe2026decisioncontracts,\n  author = {Rafe, Amir and Das, Subasish},\n"
  f"  title  = {{{meta['survey']['title']}}},\n  year   = {{{meta['survey']['year']}}},\n  note   = {{Manuscript under review}}\n}}\n```\n")
A("To cite the list itself, use [CITATION.cff](CITATION.cff) or:\n")
A("```bibtex\n@misc{rafe2026awesomesystemone,\n  author       = {Rafe, Amir and Das, Subasish},\n"
  "  title        = {{Awesome System One Models: A Curated, Evidence-Graded List of Typed Probabilistic Decision Models}},\n"
  f"  year         = {{2026}},\n  version      = {{{meta['version']}}},\n  howpublished = {{\\url{{https://github.com/{REPO}}}}}\n}}\n```\n")

# ============================================================================= cutoff
A("## 🕒 Cutoff and versioning\n")
A(f"This is **v{meta['version']}**. It reflects the survey's literature and ecosystem cutoff of **24 September 2026**, and the "
  "list is updated after it. Later additions are released as minor versions with their own cutoff date. Values are never "
  "edited in place; a correction adds a row that supersedes the old one, and model entries record the revision they describe.\n")

# ============================================================================= license
A("## 📜 License\n")
A("[![CC BY 4.0](https://licensebuttons.net/l/by/4.0/88x31.png)](https://creativecommons.org/licenses/by/4.0/)\n")
A("The list, its data files and its figures are released under [CC BY 4.0](LICENSE). Linked papers, models, datasets "
  "and repositories keep their own licenses.\n")

# ============================================================================= people
A("## 👥 Authors and maintainers\n")
prow2 = []
for p in meta["people"]:
    gh = f"<br><a href=\"https://github.com/{p['github']}\">@{p['github']}</a>" if p["github"] else ""
    prow2.append(f"<td align=\"center\" width=\"50%\">\n\n**{p['name']}**<br>{p['role']}<br>{p['affiliation']}<br>"
                 f"<a href=\"https://orcid.org/{p['orcid']}\"><img src=\"{badge('ORCID', p['orcid'], 'a6ce39')}\" alt=\"ORCID {p['orcid']}\"/></a>"
                 f"<br><a href=\"mailto:{p['email']}\">{p['email']}</a>{gh}\n\n</td>")
A('<div align="center">\n<table><tr>\n' + "\n".join(prow2) + "\n</tr></table>\n</div>\n")
A('<div align="center">\n')
A(f"![GitHub stars](https://img.shields.io/github/stars/{REPO}?style=social) "
  f"![GitHub forks](https://img.shields.io/github/forks/{REPO}?style=social) "
  f"![GitHub watchers](https://img.shields.io/github/watchers/{REPO}?style=social)\n")
A(f"<sub>Generated by <code>scripts/build_readme.py</code> from <code>data/</code>. Cutoff {meta['cutoff']}.</sub>\n")
A("</div>\n")

text = "\n".join(out).rstrip() + "\n"
with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print(f"README.md written: {len(text.splitlines())} lines, {n_resources} resources "
      f"({n_papers} papers, {len(studies)} studies, {n_models} models, {len(dataset_ids)} datasets, {len(tools)} tools)")
