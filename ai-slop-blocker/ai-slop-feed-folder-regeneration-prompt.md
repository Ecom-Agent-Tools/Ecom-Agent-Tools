# Prompt: Regenerate `ai-slop-feed-folder.user.js`

> Reverse-engineered from the userscript source. Feed this prompt to an AI to regenerate the AI Slop Feed Folder userscript from scratch.
>
> Note: the rule corpus referenced in §1 is expected to live at `AISlop/ai-slop-x-detection-rules.md` (Wisebase) — locally mirrored by `ai-slop-detection-rules-handbook-x-v2.md` in this folder.

---

You are a senior browser userscript engineer, frontend engineer, and heuristic text-classification system designer. Build a production-quality browser userscript named:

AI Slop Feed Folder

Goal: Detect, locally score, and automatically fold likely AI-generated bulk content, templated marketing copy, engagement bait, and platform spam in X/Twitter and Reddit feeds. All analysis must happen locally in the browser. Do not upload post content or call any external AI API.

━━━━━━━━━━━━━━━━━━
1. Read the Rule Corpus First
━━━━━━━━━━━━━━━━━━

The detection-rule corpus is stored in Wisebase at:

AISlop/ai-slop-x-detection-rules.md

Before writing any code:

1. Open and read the entire file.
2. Extract the following:
   - High-value positive risk signals
   - Common AI clichés
   - Templated marketing openings
   - Brand-replaceable product-pitch structures
   - Engagement bait
   - Hero-story templates
   - Reversal templates
   - List templates
   - Preachy or moralizing endings
   - Long, low-information content
   - Platform spam
   - Cryptocurrency, airdrop, promotional-link, and related signals
   - Limited-time promotions, sales urgency, and uppercase marketing copy
   - Bot-like short replies
   - Human-evidence signals that may reduce false positives
3. Treat the corpus as the primary source of truth for the detection rules. Do not arbitrarily remove important rules from it.
4. If some rules conflict, prioritize combinations of multiple independent signals. Do not classify content as AI-generated merely because it contains one ordinary word or phrase.
5. After reading the file, briefly summarize the signal categories you plan to implement before starting the script.

━━━━━━━━━━━━━━━━━━
2. Target Websites
━━━━━━━━━━━━━━━━━━

The userscript must match:

- https://x.com/*
- https://twitter.com/*
- https://www.reddit.com/*
- https://reddit.com/*

Use a valid standard userscript metadata block containing at least:

- @name
- Exactly one non-empty @description
- All four @match entries listed above
- @run-at document-idle
- One or more non-empty @changelog entries describing only the current version

The script must be implemented as a single file using native JavaScript. Do not depend on npm, build tools, or external CDNs.

━━━━━━━━━━━━━━━━━━
3. Post Detection and Text Extraction
━━━━━━━━━━━━━━━━━━

Inspect the actual DOM on the current page before designing the smallest stable selectors possible.

For X/Twitter:

- Detect `article[data-testid="tweet"]`.
- Extract tweet text from `[data-testid="tweetText"]`.
- Correctly handle multiple text sections.
- Detect whether a tweet is a reply.
- Extract a stable post ID from `/status/{id}` links.
- Support X’s infinite scrolling and DOM-node reuse as safely as possible.
- Media-only posts with no text must not cause errors.

For Reddit:

- Support the new Reddit `shreddit-post` element.
- Support common `article` and `div[data-testid="post-container"]` containers.
- Extract the post title and body.
- Extract a stable post ID from `/comments/{id}/` links.
- Support the home feed, community feeds, and modern card layouts where feasible.

Do not scan the entire page’s text. Analyze only clearly identified post containers.

━━━━━━━━━━━━━━━━━━
4. Local Scoring System
━━━━━━━━━━━━━━━━━━

Implement an explainable risk-scoring system ranging from 0 to 100.

Each scoring result must include at least:

- `score`: final risk score
- `positive`: raw positive-risk points
- `negative`: total counter-evidence or deduction points
- `positiveReasons`: reasons for adding risk points
- `negativeReasons`: reasons for deductions or counter-evidence
- `categories`: number of distinct risk categories matched

The scoring system must cover the following categories and expand them using the Wisebase corpus:

1. Templated marketing openings

   Examples include vague introductions about today’s digital age, rapidly changing industries, fast-paced environments, or ever-evolving landscapes.

2. Brand-replaceable product pitches

   Examples:

   - “X is a cutting-edge platform...”
   - “X leverages AI to...”
   - “X is designed to empower...”
   - Structures using “seamlessly,” “streamline,” “operational efficiency,” and similar language

   Treat this as a high-weight signal.

3. Generic AI clichés

   Examples:

   - delve into
   - game-changer
   - unlock the power of
   - comprehensive guide
   - valuable insights
   - harness the power of
   - ever-evolving landscape
   - in conclusion
   - key takeaways
   - holistic approach

   A single weak phrase must not generate a high score. Risk should increase substantially only when multiple phrases appear together and the content lacks factual support.

4. Engagement bait

   Examples:

   - Thoughts?
   - Agree?
   - What do you think?
   - Let that sink in
   - Read that again
   - Repost if...
   - Follow for more
   - Comment below
   - Link in bio
   - Unpopular opinion
   - Most people don’t realize...
   - Nobody is talking about this

5. Templated hero narratives

   Detect structures such as: “A few years ago, I was broke/rejected/at rock bottom. Fast forward to today, and I now run...”

6. Reversal templates

   Examples:

   - X is not Y. It’s Z.
   - It’s not about X, it’s about Y.
   - Not X, it’s Y.

7. List templates and broetry

   Examples:

   - “Here are 7 things...”
   - “10 lessons...”
   - Dense numbered or bulleted lists
   - LinkedIn-style formatting with many short one-sentence lines

8. Preachy or templated endings

   Examples:

   - The lesson is...
   - The takeaway...
   - Remember this...
   - Never give up
   - Read that again
   - The real question is...

9. Bot-like short replies

   In reply contexts, detect phrases such as:

   - Great post
   - Thanks for sharing
   - Couldn’t agree more
   - Interesting perspective
   - Well said
   - Love this insight

   This must remain a low- to medium-weight signal and must not independently cause severe folding.

10. Long, low-information content

    Add risk when a long post lacks numbers, versions, proper names, links, sources, data, test results, or other concrete details.

11. Vague authority claims

    Examples:

    - studies show
    - research shows
    - experts say
    - many companies

    Add risk when these claims lack sources, links, or specific names.

12. Platform spam

    Include, but do not limit detection to:

    - crypto
    - NFT
    - airdrop
    - presale
    - cashtags
    - Telegram or WhatsApp redirection
    - OnlyFans redirection
    - follow-for-follow
    - many consecutive @mentions

13. Urgent promotions and sales pressure

    Analyze the following only after first confirming that the text has a commercial promotional context:

    - tonight only
    - ends today
    - last chance
    - act now
    - don’t miss out
    - selling fast
    - while supplies last
    - biggest sale
    - lowest price ever
    - discount codes, prices, or percentage discounts
    - commercial links
    - repeated urgency language
    - high-density uppercase marketing copy

    News, weather alerts, disasters, sporting events, system maintenance, and security alerts must not be treated as promotions merely because they contain words related to deadlines or alerts.

━━━━━━━━━━━━━━━━━━
5. Human Evidence That Reduces False Positives
━━━━━━━━━━━━━━━━━━

Detect and record the following forms of counter-evidence:

- First-hand experience:
  - I tried
  - I tested
  - We tested
  - I built
  - I shipped
  - My setup
  - In my case

- Concrete numbers:
  - Percentages
  - Years
  - Currency amounts
  - Units such as milliseconds, GB, FPS, and QPS
  - Software version numbers

- Technical evidence:
  - GitHub links
  - curl commands
  - stack traces
  - error logs
  - benchmarks
  - datasets
  - papers, DOIs, and sources

- Specific disagreement or tradeoffs:
  - I disagree
  - That depends
  - The tradeoff
  - Counterexample
  - however ... because ...

- Natural informal language:
  - tbh
  - imo
  - idk
  - fwiw
  - lol
  - ugh
  - edit:
  - typo
  - iirc

- On X, verified institutional or government accounts may receive a small counter-evidence adjustment. Ordinary accounts with paid blue verification must not automatically be treated as trustworthy.

Important requirements:

- Counter-evidence must be shown in the explanation panel.
- Explicitly decide whether counter-evidence is “observational only” or actually reduces the final score.
- If it reduces the score, cap the maximum deduction so spam or marketing copy cannot evade detection merely by inserting a few numbers.
- High-confidence promotional spam must not be easily canceled out by weak counter-evidence.

━━━━━━━━━━━━━━━━━━
6. Scoring Design Principles
━━━━━━━━━━━━━━━━━━

Use maintainable configuration objects and helper functions rather than one large block of opaque conditions.

Requirements:

- Clamp the final score to the 0–100 range.
- High-value structural signals must outweigh pure stylistic signals.
- Stylometric signals—such as uniform sentence length, lack of contractions, emoji density, or bullet density—must add only a small number of points.
- A single weak signal must not independently trigger high risk.
- Matching several independent categories may apply a multi-signal multiplier.
- Reduce the effect of weak signals on very short posts.
- Long but vague posts may receive a moderate risk increase.
- Deduplicate all explanation reasons.
- Use a bounded text-scoring cache, such as a maximum of approximately 1,000 entries, to prevent unbounded memory growth.
- Use a deterministic hash as a stable tie-breaker when posts receive equal scores.
- Do not use random classification.

Provide three strictness presets stored in `localStorage`:

- `relaxed`
- `balanced`
- `aggressive`

The default must be `balanced`.

Also provide action modes:

- `fold`: fold high-risk content
- `hide`: completely hide only extremely high-risk content
- `mark`: visually mark suspicious content that remains below the folding threshold

Design reasonable and internally consistent `mark`, `fold`, and `hide` thresholds. Do not define a folding threshold but then bypass it with a hardcoded constant elsewhere in the implementation.

━━━━━━━━━━━━━━━━━━
7. Feed-Level Calibration
━━━━━━━━━━━━━━━━━━

In addition to absolute scores, the script may maintain a risk ranking for approximately the 300 most recent posts in the current feed to reduce scoring differences between feeds.

Requirements:

- X and Reddit may use different calibration ratios.
- Ranking-based calibration may trigger folding only if a post also reaches a minimum absolute-risk threshold.
- Do not force clearly normal posts to fold merely to satisfy a fixed folding ratio.
- Calibration rankings must be deterministic and stable.
- The folded placeholder may display text such as:
  `calibrated top 24% (3/120)`
- If variables such as `foldCount` or a calibration ratio are implemented, they must actually participate in the logic. Do not leave dead or ineffective variables.

━━━━━━━━━━━━━━━━━━
8. Page UI and Interaction
━━━━━━━━━━━━━━━━━━

Display one compact, deduplicated risk scorecard for every analyzed post.

Scorecard requirements:

- Show the final risk score, such as `67`.
- Allow the user to expand it to view:
  - Positive risk signals
  - Counter-evidence or deductions
- Never insert duplicate scorecards.
- On X, place it near the avatar when possible without covering the content or native controls.
- On Reddit, place it near the author or credit bar when possible.
- Use system fonts.
- Support both light and dark themes.
- Do not use external icons or resources.

Mark mode:

- Use a restrained orange edge or compact label.
- The label may say `AI slop risk 67`.

Fold mode:

- The original post content must be invisible and non-interactive.
- Replace it with an independent compact placeholder.
- The placeholder must display:
  - Risk score
  - A few primary reasons
  - Optional calibration rank
  - A Reveal button
- Only the Reveal button should trigger restoration.
- Clicking Reveal must not click through to links or native controls inside the post.
- Reveal must restore the complete post.

Hide mode:

- Only posts that reach the `hide` threshold may use `display: none`.
- Other high-risk posts must still use fold mode.

Do not automatically reveal folded content on hover or focus.

━━━━━━━━━━━━━━━━━━
9. Persistent Reveal State
━━━━━━━━━━━━━━━━━━

A post manually revealed by the user must not be immediately folded again after rescanning or refreshing the page.

Requirements:

- Save revealed posts using stable post IDs.
- Use the status ID on X.
- Use the comments ID on Reddit.
- Keep at most approximately 1,000 IDs in `localStorage`.
- If no stable ID can be extracted, preserve the revealed state only for the current DOM lifecycle.
- Respect the user’s reveal choice during rescans, DOM reuse, and infinite scrolling.

━━━━━━━━━━━━━━━━━━
10. Dynamic Pages and Performance
━━━━━━━━━━━━━━━━━━

X and Reddit are dynamic applications. Safely handle infinite scrolling and DOM updates.

The script must:

- Run one initial scan.
- Use narrowly scoped `MutationObserver` instances.
- Debounce rescans by approximately 150–250 milliseconds.
- Use a `WeakMap` to record each post’s last processed text and context to avoid redundant scoring.
- Use a bounded `Map` for feed-calibration records.
- Give all inserted elements unique classes or data attributes.
- Avoid adding duplicate styles, listeners, timers, or observers if the script runs more than once.
- Avoid unbounded timers, caches, and high-frequency full-page layout recalculation.
- Give observers a cleanup strategy or otherwise ensure their scope and cost remain controlled.
- Prevent long-running pages from retaining unlimited references to posts that have left the DOM.
- Remain stable across SPA route changes and DOM-node reuse.

━━━━━━━━━━━━━━━━━━
11. Security and Engineering Constraints
━━━━━━━━━━━━━━━━━━

- Use an IIFE and `'use strict'`.
- Do not replace `document.body`, `document.documentElement`, or the website’s main application root.
- Do not use `document.write`.
- Do not patch browser prototypes.
- Do not override website globals.
- Do not make network requests.
- Do not collect, upload, or log the user’s browsing content.
- Do not use `innerHTML` to insert unescaped post text.
- Use `textContent` for all displayed post text and explanation reasons.
- Add styles using `siderRuntime.addStyle()` or by safely creating a `<style>` element.
- If using `siderRuntime`, use only APIs that actually exist and are allowed by its documentation.
- The code must be idempotent.
- Do not depend on obfuscated CSS classes.
- Handle missing selectors, absent DOM elements, and future website layout changes gracefully.

━━━━━━━━━━━━━━━━━━
12. Required Implementation Workflow
━━━━━━━━━━━━━━━━━━

Follow this sequence exactly:

1. Read the rule file from Wisebase.
2. Inspect the minimum relevant DOM for:
   - One ordinary X post
   - One X reply
   - The X feed container
3. If Reddit support is required, also inspect the minimum relevant DOM of a modern Reddit post card.
4. Output a short implementation plan.
5. Write the complete userscript draft.
6. Validate it through temporary execution before saving:
   - It detects posts.
   - It extracts the correct text.
   - The scoring function has no syntax or runtime errors.
   - It does not insert duplicate scorecards.
   - Folded original posts cannot receive clicks.
   - Reveal restores the post correctly.
   - A revealed post is not immediately folded again by the observer.
   - New posts added through infinite scrolling are analyzed.
   - Reddit and X selectors do not interfere with each other.
7. Fix all issues discovered during validation.
8. Save only one final userscript version.
9. Output:
   - A summary of completed features
   - The main thresholds
   - The `localStorage` configuration keys
   - Known limitations
   - The complete final code

━━━━━━━━━━━━━━━━━━
13. Acceptance Criteria
━━━━━━━━━━━━━━━━━━

The final script must satisfy all of the following:

- It runs in the X and Reddit home feeds.
- It analyzes newly added posts without reloading the page.
- Every risk score is explainable.
- High-value structural signals have substantially more weight than pure writing-style signals.
- Normal technical posts, first-hand experience, and specific disagreements are less likely to be misclassified.
- High-pressure promotions, brand-replaceable product pitches, stacked engagement bait, and templated long-form content receive high scores.
- High-risk posts are genuinely replaced by compact placeholders rather than merely blurred or made transparent.
- Folded original posts cannot receive clicks.
- Reveal clicks do not pass through to the original post.
- The user’s reveal choice persists.
- The script does not create duplicate scorecards, duplicate listeners, or obvious memory leaks.
- It does not depend on a server or external AI model.
- The code is clearly structured and easy to extend with additional rules.

Do not provide only pseudocode or an explanation. Complete the DOM inspection, implementation, temporary validation, and final userscript save.
