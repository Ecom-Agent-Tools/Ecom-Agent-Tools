# Prompt: Original (v1) — Generate `ai-slop-feed-folder.user.js`

> The original, short prompt that first produced the AI Slop Feed Folder userscript.
>
> Companion files:
> - Detailed reverse-engineered prompt: `ai-slop-feed-folder-regeneration-prompt.md`
> - Rule corpus: `ai-slop-detection-rules-handbook-x-v2.md` (local mirror of Wisebase `AISlop/ai-slop-x-detection-rules.md`)
> - Output: `ai-slop-feed-folder.user.js`

---

Build me a privacy-friendly userscript called "AI Slop Feed Folder" that works on X and Reddit. Read my detection notes from Wisebase at AISlop/ai-slop-x-detection-rules.md, then use those rules to score posts locally from 0–100 and fold likely AI spam, templated marketing, engagement bait, fake inspirational stories, bot replies, and low-information content.

Show a small explainable score on each post, and replace high-risk posts with a compact placeholder containing the score, the main reasons, and a Reveal button. Concrete numbers, sources, technical evidence, first-hand experience, and specific disagreement should reduce false positives. Remember revealed posts in localStorage so they stay revealed.

Support infinite scrolling, modern X and Reddit layouts, light/dark themes, three sensitivity levels, and mark/fold/hide modes. Keep it lightweight and idempotent, with no external AI calls, uploaded post data, duplicate UI, or memory leaks.

Inspect the current DOM and test the draft before saving. Make sure folded posts can't be clicked, Reveal doesn't click through, and dynamically added posts are processed. Then save one complete working userscript for x.com, twitter.com, reddit.com, and www.reddit.com—not pseudocode.
