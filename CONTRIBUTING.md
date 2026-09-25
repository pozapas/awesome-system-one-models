# 🤝 Contributing to Awesome System One Models

<div align="center">

**Thank you for helping keep this list accurate and current.** 🎯

*Every entry is traceable to a public source, and every table is generated from the files in `data/`.*

[![Contributors Welcome](https://img.shields.io/badge/Contributors-Welcome-brightgreen.svg?style=flat-square)](https://github.com/pozapas/awesome-system-one-models/graphs/contributors)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-blue.svg?style=flat-square)](https://github.com/pozapas/awesome-system-one-models/pulls)

</div>

---

## 🌟 What belongs here

This list accompanies the survey *From Calibrated Classifiers to Decision Contracts: A Survey of System One Models* (Rafe and Das, manuscript under review). It covers typed probabilistic decision models, meaning models that map a state and a caller-declared typed question (Choice, Score or Noul) to a probability distribution over a finite answer space without generating text, together with the research lines, datasets, tools and evidence around them.

The inclusion rules follow the survey's evidence protocol.

| Kind | Included when | Not included |
| --- | --- | --- |
| 📄 **Study** (evidence table) | It reports a measured quantity for a typed probabilistic decision model on a stated task against a stated reference. Papers, model cards, repositories and posts all qualify if they report such a measurement. | Tutorials that report no measurement, directories built for search traffic, and marketing copy without a protocol. |
| 📚 **Paper** (genealogy and related resources) | It belongs to one of the five streams (label-conditioned heads, reward models and judges, proper scoring and calibration, the reject option and cascades, dual-process architectures) or to an adjacent line, and its metadata resolves in a registry (Crossref, DataCite, arXiv, DBLP or OpenAlex). | Items without a resolvable DOI, arXiv ID or stable URL. |
| 🤖 **Model** (census) | An open original implementation (tier T1) with its own recipe or decision head and a public card, or a hosted model with public documentation. | Pure format conversions, quantizations, merges and re-uploads (tier T2). These are counted in the derivative table rather than listed. |
| 🗃️ **Dataset** | A public dataset whose card states that its items are typed decisions (Choice, Score or Noul) and states how its labels were made. | Generic classification sets that were not built for the typed contract (they may appear as benchmarks reused in the evidence). |
| 🛠️ **Tool** | A public repository that serves, calls, trains or evaluates a decision model, with a license and a README that states what it does. | Plug-ins for coding assistants, which are counted in the census but not listed individually. |

## 🚀 How to contribute

### 1. Open an issue (the easiest route)

Use one of the issue forms, and the maintainers will add the entry.

- [📄 Add a paper or study](https://github.com/pozapas/awesome-system-one-models/issues/new?template=add-paper.yml)
- [🤖 Add a model, dataset or tool](https://github.com/pozapas/awesome-system-one-models/issues/new?template=add-model.yml)
- [🩹 Report a correction or a dead link](https://github.com/pozapas/awesome-system-one-models/issues/new?template=correction.yml)

### 2. Open a pull request

The README is generated, so please edit the data files and not the README tables.

```bash
# 1. Fork the repository and create a branch
git checkout -b add-<short-name>

# 2. Add or edit rows in the relevant file under data/
#    papers.csv        papers in the genealogy streams and related resources
#    studies.csv       studies in the evidence table
#    census_t1.csv     open original implementations (one row per checkpoint)
#    families.csv      the condensed family table
#    datasets.csv      typed-decision datasets with a full card
#    tooling.csv       harnesses, servers, SDKs and evaluation packages

# 3. Rebuild the README (Python 3, standard library only)
python3 scripts/build_readme.py

# 4. Commit the data change and the rebuilt README together
git commit -am "Add <resource name>"
```

### 3. Field rules

| File | Required fields | Notes |
| --- | --- | --- |
| `papers.csv` | `group`, `year`, `title`, `first_author`, `venue`, `link` | `group` is one of `S1` to `S5`, `ADJ`, `RPT`, `STATS` or `DATA`. `link` is a DOI URL, an arXiv abstract URL or a stable publisher URL. |
| `studies.csv` | `title`, `link`, `date`, `task_family`, `decision_models`, `reference_labels` | Leave `rob_overall` empty. The maintainers grade every study on the five risk-of-bias domains before it is listed. |
| `census_t1.csv` | `id`, `created`, `license`, `base_model` | `id` is the Hugging Face repository ID. Fill `head` (`a` to `e`) only when the card describes the decision head. |
| `datasets.csv` | `id`, `author`, `license`, `purpose` | `purpose` is a sentence taken from the card. |
| `tooling.csv` | `name`, `repo`, `category`, `license`, `description` | `category` is one of `vendor_sdk`, `local_server`, `integration`, `evaluation` or `open_model_training`. |

## 🔬 How studies are graded

Each study in the evidence table is rated low, unclear or high on five domains adapted from PROBAST and QUADAS-AI, and the overall grade shown as a badge follows from them.

1. **Reference-label independence.** Human adjudicated labels count as low risk; crowd labels as low or unclear; teacher-model, model-consensus or vendor labels as high; administrative fields as unclear.
2. **Sampling design and reporting**, including the sample size and any interval.
3. **Version pinning and access dates** for every hosted model and checkpoint.
4. **Tuning-budget parity** between the compared systems.
5. **Test-set exposure**, meaning whether the items predate the models or appear in public training data.

A grade describes the evidence behind a study's numbers, not the quality of the models it tests. If you think a grade is wrong, open a correction issue and cite the passage in the study.

## 🕒 Versioning and corrections

- The list reflects the survey cutoff of **24 September 2026** as version **v1.0**. Later additions are released as minor versions (v1.1, v1.2 and so on), each with its own cutoff date.
- Values are never edited in place. A correction adds a row that supersedes the old one, so the history stays auditable.
- Model entries record the revision or creation date they describe, because a served checkpoint can change behind an unchanged name.

## ✅ Before you submit

- [ ] The resource is public, and every link opens.
- [ ] The entry meets the inclusion rule for its kind.
- [ ] Numbers or claims are copied from the source, not paraphrased into new values.
- [ ] `python3 scripts/build_readme.py` runs without a count mismatch.
- [ ] The pull request touches only the data files and the regenerated README.

## 🙌 Code of conduct

Please be respectful and specific. Disagreements about a grade or a classification are welcome when they point to the source text.

---

<div align="center">

Questions? Open an issue or write to the maintainer, [Amir Rafe](mailto:amir.rafe@txstate.edu).

</div>
