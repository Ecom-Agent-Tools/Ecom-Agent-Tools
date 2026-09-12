# AI Slop Detection Rules Handbook — X.com Edition v2.0

**Purpose:** For the Sider extension to pre-judge whether post content on X.com pages is "AI slop." Hit → collapse; no hit → keep.

**v2.0 changes:** Based on 865 real dead/flagged entries from `data/hn-flagged-dead/` plus 3228 full post bodies containing AI-slop characteristic phrases, v1's signal weights were empirically calibrated using real corpus data — proving that a "single keyword blacklist" is unreliable, elevating "marketing-tone opening + brand replacement test" to the highest-confidence signal, and downgrading "bot-style agreement phrases."

**Data sources:**

- `hn_dead_flagged_865.json` (865 dead/flagged entries, with author/type/time metadata)
- `hn_ai_slop_corpus_3228.json` (3228 full comment bodies containing 22 categories of characteristic phrases)
- `HN-flagged-dead共同点分析.md` (qualitative analysis already completed)
- Plus what v1 already had: `projects/ai-slop-blocker/`, `research/ai-slop-competitors/extensions/`, `skills/content-humanizer/`, `data/x-ai-smell-governance-report.md`

**Date:** 2026-08-20

---

## 0. Judgment Framework (unchanged core principles)

1. Judge "low-quality risk," not "whether it was written by AI." AI-assisted but useful ≠ slop.
2. Conservative first: better to miss than to falsely kill. Precision > Recall. Falsely killing real users destroys trust.
3. Judge only when multiple signals stack; a single signal is insufficient (v2 reinforced this with real data).
4. Human signal guardrails (negative rules): specific numbers / first-hand experience / technical details / reasoned disagreement / source links → significantly reduce the score and protect.
5. Three tiers of action: low risk = badge / medium risk = fold (expandable) / high risk = hide (strict mode).
6. Trusted account exemption: verified accounts (blue check / institutional) are skipped by default.
7. Plain text is a cat-and-mouse game: combining account behavior (new account + high posting density) is more robust.

---

## 1. v2 Core Addition: Empirically Calibrated Conclusions (What Real HN Data Taught Us)

This is the most important upgrade in v2 over v1. Using 3228 full HN comments containing characteristic phrases, a signal reliability grading was performed (which ones truly distinguish slop and which are noise).

### 1.1 Signals Proven [Reliable] (True High Confidence)

**① Marketing-tone opening + product-placement structure (strongest signal, almost 100% advertorial)**

The real flagged HN advertorials are almost all "Wikipedia-style lead-in + product name + feature stacking" templates:

- "In the ever-evolving landscape of real estate and proptech, connecting buyers and sellers efficiently remains one of the biggest challenges. Offa.com is emerging as a top-tier AI-powered platform designed to match buyers..."
- "In today's digital landscape, understanding website traffic is essential for businesses... Free Website Traffic Checker is a powerful tool..."
- "RTILA is a cutting-edge web business automation tool designed to empower agencies... AI-driven solutions... seamlessly... streamlines processes..."

Judgment core = the **"brand replacement test"**: Replace the product/company name with any other name and the sentence still reads smoothly and holds up → it is a template advertorial with no unique information. This is the highest-confidence, least error-prone signal.

**② Vague superlatives + marketing-word density (requires 2+ and no factual support)**

- `cutting-edge` / `revolutionize` (162 hits in the corpus, and the only buzzword with a URL rate as high as 38/147)
- `leverage` (211 hits)
- `seamlessly` / `empower` / `streamline` / `AI-powered` / `AI-driven` / `unlock the full potential` / `harness the power`

Judgment point: 2 or more such words in a passage + no specific facts/numbers/personal experience = high risk.

```
(X|Y|Z) is a (cutting-edge|powerful|top-tier|innovative) (tool|platform|solution|app)
(X) (leverages|uses|employs) (cutting-edge|AI-powered|AI-driven) (AI|technology) to
(X) (is designed to|aims to|enables) (empower|streamline|revolutionize|transform)
seamlessly / streamlines processes / enhances operational efficiency
```

### 1.2 Signals Proven [Unreliable] (Frequently Used by Real People — Don't Use Alone as Evidence)

In the real corpus, these "AI-smelling words" appear in large numbers in normal people's normal comments:

| Word/phrase | Corpus hits | Measured conclusion |
| --- | --- | --- |
| game-changer | 150 | Commonly used by real people ("AWS VPC is a game-changer for privacy" was written by a real person) |
| leverage this | 149 | Many are literal usage in technical discussion ("an armbar works on the principle of leverage") |
| delve into | 149 | buzz=0, mostly real people "delve into the codebase" |
| a testament to | 150 | Mostly idiomatic real-person usage |
| In recent years | 150 | buzz only 3, basically a normal academic/narrative opening, not slop |
| furthermore / moreover / additionally | 320 / 166 | Academic tone, commonly used by real people |
| great article! / well said / couldn't agree more / great point | 146 / 121 / 143 / 139 | Largely genuine substantive real-person interaction ("Great article, key points: ..." followed by real analysis) |

**Lesson (v2 hard rule):** A single-point judgment based on a keyword blacklist is prohibited. Things like `well said` and `couldn't agree more`, which in v1 were listed as bot signals, are in practice commonly used by real people — v2 must downgrade them, and they only matter in "short reply + no subsequent substantive content."

### 1.3 Signals Proven [Require Context]

- Customer-service-tone closing `I hope this helps` (123) / `Let me know if you have any questions` (164):
  In practice, many are real founders normally saying "Author here... Let me know if you have any questions" in launch/Show HN posts. → Cannot be judged as slop on its own; only suspicious when combined as "vague content + customer-service-tone closing."

---

## 2.2 🟡 Medium Confidence (Needs Stacking)

**D. Generic AI phrasing (generic AI phrasing)**

**H. Stylometric features (stylometric, weak signal, needs stacking)**

| Feature | Judgment | Weight |
| --- | --- | --- |
| Sentence-length uniformity (CV < 0.2–0.3, ≥4 sentences) | Mechanical | +2 |
| Long text without contractions (>40 words and 't/'s/'re=0) | Reply too formal | +1–2 |
| Superlative stacking (excellent/fantastic/brilliant… ≥3) | Flattery | +2 |
| em-dash/ellipsis density (≥1.0/sentence) | AI fingerprint | By density |
| emoji density (≥5 or >0.1/word) | Over-polished | +2–5 |
| broetry (line breaks >10 and average length <50 chars) | One sentence per line | +5 |
| bullet/arrow lists (3+ line starts) | Template | +3–6 |
| hedge density (essentially/basically/arguably high frequency) | Overly safe | By density |
| Low information density (>110 words but specific numbers/proper nouns <3) | Long but empty | +20 |
| Insufficient specificity ("many companies" "studies show" with no names) | Vague | +16 |

⚠️ **v2 warning** (from the governance report + HN corpus): Do not use TTR, AI-detector scores, dashes, or first person as hard rules — on short posts they all deceive.

v2 scoring: A single hit scores nothing (HN proved real people commonly use it); only when "reply <22 words + hit + no specific content whatsoever" → +12.

---

## 4. Human Signal Guardrails (Negative Rules — Protect Real People)

- **First-hand details:** i tried / i used / my setup / in my case / we tested / i built / i shipped
- **Specific numbers:** $N / N% / v2.3 / version N / date / Nms / Ngb / year
- **Technical/sources:** error log / stack trace / github.com / api key / curl / npm run / screenshot / source: / dataset / paper
- **Reasoned disagreement:** i disagree / not quite / that depends / the tradeoff / counterexample / however + because
- **Colloquial/informal:** tbh / imo / idk / fwiw / lol / ugh / honestly / edit: / typo / iirc
- **Specific people/things:** real customer quotes, specific product names, verifiable events, replies with substantive content

---

## 5. LLM Deep Judgment (Optional, Called Only in the Borderline Range)

Called only for borderline content with score ∈ [mark−8, hide], to save cost and reduce false positives.

**System Prompt (a conservative reviewer incorporating the HN corpus):**

```
You are a conservative feed-quality reviewer for an X.com AI Slop Blocker.
Judge low-quality feed risk, NOT whether the author is AI.

AI Slop = generic, repetitive, promotional, template-like, engagement-bait,
bot-like, or crypto/spam content with little specific value.

Rules:
- Prefer false negatives over false positives.
- Short casual replies are often normal on X.
- Do not punish posts discussing AI/LLMs as a topic.
- A single buzzword (leverage, game-changer, delve) is NOT evidence.
- The strongest signal is the "brand replaceability test": if you can swap the
  product/company name for any other and the sentence still works, it's template spam.
- Technical errors, source links, screenshots, version numbers, benchmarks,
  and reasoned disagreement are strong CLEAN signals.

Return JSON only:
{"risk":"clean|watch|slop","confidence":0-1,"scoreAdjustment":-30..30,"reasons":["short reason"]}
```

Template patterns used for reference:

```
is a (cutting-edge|powerful|top-tier|innovative) (tool|platform|solution|app)
leverages (cutting-edge|AI-powered|AI-driven) (AI|technology)
is designed to (empower|streamline|revolutionize|transform)
seamlessly / streamlines processes / enhances operational efficiency
AI-powered / AI-driven / AI-assisted
```

---

## 6. X.com Implementation Notes

- **DOM extraction:** `[data-testid="tweetText"]` / container `article[data-testid="tweet"]`. For SPAs, use MutationObserver + debounce, with IntersectionObserver prioritizing in-viewport items.
- **Minimum length threshold:** ≥30–40 characters, to prevent empty/very short misjudgments.
- **Trusted account exemption:** verified/institutional badge → skip.
- **Deduplication/caching:** `WeakMap<HTMLElement, textKey>` + text hash cache.
- **Collapse UI:** placeholder card (score + reason badges + Reveal / Not slop / Hide more like this). Default to Fold rather than hide.
- **Local feedback learning:** Not slop → local whitelist hash; Hide more → extract evidence phrases, making similar content easier to fold later.
- **Privacy:** The rules engine is purely local with zero uploads; only borderline content is sent to the LLM on demand.
- **v2 emphasis:** Run the two P0 signals — "brand replacement test + marketing-tone opening" — first, then the buzzword combination, and only lastly the weak stylistic signals — to avoid falsely killing real people.

---

## 7. Rule Priority Quick Reference (v2 Reordered, by Empirical Confidence)

| Priority | Signal | Action |
| --- | --- | --- |
| P0 (empirically strongest) | Marketing-tone opening + product placement + failed brand replacement test | fold |
| P0 | X spam signals (crypto/OF/Telegram + link) | fold/hide |
| P1 | Buzzword stacking (2+ with no facts) + template structure + link cluster | fold |
| P1 | Hero story / reversal syntax / preachy ending (2 categories stacked) | fold |
| P2 (weak, needs stacking) | Single cliché / single dash / emoji density / uniform sentence length | badge only |
| Guardrails (never falsely kill) | Verified account / specific numbers / first-hand details / technical sources / reasoned disagreement | keep |
| v2 downgraded | well said / couldn't agree more / great article / single buzzword | no score on their own |

---

*Note: The source file's content was retrieved in topical chunks, so the retrieved excerpts don't cover every section in the original order — sections like 2.2 D (generic AI phrasing) and the middle of the stylometry table appeared only partially. Section numbering gaps (1.3 → 2.2, 2.2 → 4, 4 → 5) reflect the source document's own structure.*
