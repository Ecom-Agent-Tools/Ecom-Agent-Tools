# AI Slop Blocker

[English](README.md) | [简体中文](README.zh-CN.md)

A personal experiment built with Sider Code to score and fold low-quality posts in X and Reddit feeds. Part of [Ecom-Agent-Tools](https://github.com/Ecom-Agent-Tools/Ecom-Agent-Tools).

The aim is to spend less attention on generic pitches, engagement bait, repetitive templates, and low-information posts. AI-assisted writing can be useful; human-written content can be slop. A higher score means more matching risk signals, **not a statistically calibrated probability that a post was written by AI**.

## Files

| File | Purpose |
| --- | --- |
| [Detection rules handbook](ai-slop-detection-rules-handbook-x-v2.md) | English rule reference, mirrored from Wisebase; its title and examples focus on X. |
| [Original prompt](ai-slop-feed-folder-original-prompt.md) | Short prompt used to request the initial script. |
| [Regeneration prompt](ai-slop-feed-folder-regeneration-prompt.md) | Detailed reconstruction requirements; these describe intended behavior, not a guarantee that the saved script implements every requirement. |
| [Userscript](ai-slop-feed-folder.user.js) | Saved JavaScript snapshot, version 3.0.0, for X/Twitter and Reddit. |

The raw Hacker News datasets and article screenshots are not included. The handbook references 865 dead/flagged entries and another 3,228 comment bodies containing characteristic phrases. Those counts describe its stated source material, not files shipped here. Dead/flagged status does not establish AI authorship or prove that an item is slop. The handbook also notes that its source was retrieved in excerpts.

## Recreate it with Sider Code

1. Open [Sider Code](https://sider.ai/agents/code) in the Sider browser extension.
2. Upload the detection rules handbook to your own Wisebase. The prompts use `AISlop/ai-slop-x-detection-rules.md`; replace that reference with your actual document location, or store the document there.
3. Open X or Reddit, select Code, and provide the original prompt. Ask it to read the Wisebase document before generating the script.
4. Use the regeneration prompt if you want more detailed requirements. Specify your own folding policy and ask Code to inspect the current page layout.
5. Review the generated script, save/enable it through Code, and check scoring, folding, Reveal, and newly loaded posts on both platforms.

You can also give Code the saved `.user.js` file as a starting point. It is a browser userscript, not a standalone extension package. Current site compatibility has not been independently browser-tested as part of this documentation update.

## What the saved script actually does

- Scores extracted post text locally using JavaScript rules and displays a compact scorecard with reasons. On X it positions the card below the avatar when that element is available; on Reddit it uses the identity row or the post container.
- Folds posts with a Reveal control and remembers revealed post IDs in `localStorage`.
- Watches for page changes to process newly loaded posts.
- Contains no external AI calls or post-upload requests. This describes this script's scoring logic, not the Sider extension's overall data handling.

**This is an experimental snapshot with differences from the prompts:**

- The active folding condition is `result.score > 21` on both platforms.
- `calibrationRate` is `0.24` for X and `0.14` for Reddit, but percentage-based folding is inactive: `recalibrate()` passes `calibratedFold: false`, and the calculated `foldCount` does not decide folding. Changing these ratios alone will not change the folding boundary.
- Evidence such as first-hand details and technical sources appears in the displayed negative-signal breakdown, but that negative total is not subtracted from the final score. Some scoring rules separately check factual support.
- The script reads strictness/action settings, but its fixed folding condition bypasses the configured `fold` thresholds; `mark` does not reliably mean “never fold.”
- The script scores promotional language and does not implement a general exemption for platform ads.

## Choose a boundary for your own feed

In the author's manual experiment, slop became conspicuous around the highest-scoring 10% of sampled X posts and 6% of sampled Reddit posts. The author then chose broader boundaries around the top 15% and 9%, respectively. These are personal observations and preferences, not platform-wide prevalence estimates or validated accuracy measurements. **The saved script does not implement those two percentage boundaries.**

To reproduce the calibration process, score several hundred posts from your own feed on each platform separately. Review from the highest scores downward, including posts around the prospective cutoff. Choose the score boundary you are comfortable with and check what gets folded. A percentile in a sample does not guarantee the same folding percentage in future feeds, especially when scores tie or the feed changes.

Give Code the resulting platform-specific policy and verify that it participates in the actual folding logic. If you want ads to remain visible, request and test that separately. The rules are mainly English-language heuristics; other languages and image/video-only posts need separate evaluation.
