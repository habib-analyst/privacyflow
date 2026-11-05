# G1 — Live author-code recheck for arXiv 2610.40714 (PrivacyFlow)

Checked: 2026-11-02, before any experiment number was generated.
Paper: "PrivacyFlow: Privacy in AI Agents through Information Flow Analysis and
Consequence-Aware Risk Management" — Robin Staab, Tom Wollschläger, Vahab
Mirrokni, Reza Shokri. Submitted 29 Oct 2026. arXiv:2610.40714.

## 1. arXiv abstract page (https://arxiv.org/abs/2610.40714)
- Authors confirmed as above; affiliations Google Research / ETH Zurich.
- "Code, Data and Media Associated with this Article" section lists only
  generic toggles (alphaXiv, CatalyzeX, DagsHub, GotitPub, Hugging Face,
  ScienceCast, Replicate, Spaces, TXYZ.AI). NO author code/data link is
  displayed. No "Code" tab with an author repository.

## 2. Full-text HTML scan (https://arxiv.org/html/2610.40714v1, 2631 lines)
Searched the full rendered text, including ALL figure captions:
- `github` / `github.com`: exactly ONE hit — reference [24] in the bibliography
  citing https://github.com/openclaw/openclaw (OpenClaw, 2026), a third-party
  deployment the paper's pilot study ran against. NOT author code.
- `code is available`: 0 hits. `open source`: 0 hits. `repository`: 0 hits.
- `available`: 4 hits, all generic ("data available to a conversational
  agent", "tools available", "available to the executor") — none a code release.
- `release`: hits refer only to "the 986 released sequences" / "released
  version of PrivacyBench" (the benchmark as described in the paper), with
  NO link, URL, DOI, or repository name attached.
- Figure captions scanned individually: Fig. 1 (PrivacyBench/PrivacyFlow
  overview), Fig. 2 (agent interaction), Fig. 3 (generation pipeline),
  Fig. 4 (PrivacyFlow architecture: Triage/Plan/Inference/Flow/Ver­dict),
  Fig. 5–8 (main results), Fig. 9–12 (appendix results), Fig. 13 (worked
  example). NONE mentions code, a repository, GitHub, or a URL. This is the
  caption sweep the #123 blindtochange lesson requires — no author repo is
  hidden in a caption.

## 3. Web search for title/authors + code
- Query "PrivacyFlow Staab Wollschläger Mirrokni Shokri GitHub code": no
  author repository. Top hits are unrelated (privacy-flow-inspector PyPI
  package by another author, Privacy Parser, PrivacyFL federated learning).
- Query "\"PrivacyBench\" \"PrivacyFlow\" Staab code repository": no author
  repository; hits are a different, older PrivacyBench (IIIT Hyderabad,
  conversational benchmark) and unrelated benchmarks.

## Verdict: G1 PASS — no author code found.
Caveat recorded honestly: the paper was submitted only 4 days before this
check (29 Oct 2026), so author code could appear later; this verdict covers
the live sources above on 2026-11-02. This build is therefore an independent,
from-scratch, scripted analog — NOT a reproduction of author code, and it
must never be described as the authors' implementation.
