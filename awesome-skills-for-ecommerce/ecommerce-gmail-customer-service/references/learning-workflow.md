# User email learning and continuous memory

## Table of contents

1. Authorization and privacy boundaries that cannot be bypassed
2. First 30 days of history study
3. User confirmation tone scheme
4. Three-level classification processing plan
5. Continuous learning from manual modification of Draft
6. Retrieve memory before replying
7. Memory update JSON structure

## 1. Authorization and privacy boundaries that cannot be bypassed

- Any learning will only be performed if the user explicitly agrees to it during the current configuration process and if `learning.enabled=true` is set in `config.json`.
- When the user rejects, does not answer, or subsequently closes, historical emails are not searched, Draft baselines are not established, and memory is not read or written for replies; normal customer service processes continue to run.
- If the mailbox is not a dedicated customer service mailbox, first ask the user to provide the customer service label, sending domain, receiving alias or other Gmail query range; do not scan obvious personal or employee emails.
- The historical window is fixed to 30 days before the authorization time. By default, attachments are not downloaded, external links are not opened, the original text is not saved, or the complete email is exported.
- Only save the desensitization summary in the local running directory. Do not include name, email, phone number, address, order number, tracking number, payment information, identification, health information or other customer-specific information.
- Users can view, modify or close studies. Closing only stops subsequent reading and writing; deleting existing memory is a separate operation and must be explicitly authorized again.

## 2. First 30 days of history study

After the mailbox reading verification is successful, ask as it is:

> Gmail can now be read normally. Do you allow me to read the emails from this customer service mailbox in the past 30 days to summarize your response tone, common words and how you handle different customer issues? By default, attachments are not downloaded and the original email is not saved. Only the desensitized summary is written to the local user_memory.md. You can decline or close anytime later.

After the user agrees:

1. Run `python3 scripts/configure.py set learning on` to record the consent time.
2. For dedicated customer service emails, use `newer_than:30d` to pull all pages; for non-dedicated email addresses, first narrow the query to the label, alias or domain confirmed by the user.
3. Take the thread containing the reply sent by the merchant as the main sample, pull the receipt and sending text in the thread in the past 30 days, and reconstruct "Customer problem → Merchant reply → Follow-up results". Attachments are not downloaded.
4. Exclude automatic notifications, marketing mass mailings, internal emails, spam emails, pure system receipts, threads without customer questions and content that cannot be confirmed to be manual responses from the merchant.
5. Complete the analysis in memory; discard the original text after processing a batch, and do not create a corpus of original emails.
6. Output coverage: start and end dates, search query, number of threads, number of available manual replies, number of excluded items and reasons. Output and logs are desensitized.

## 3. User confirmation tone scheme

Summarize it first but don’t activate it directly. At least include:

- Address and opening method;
- Empathy intensity and apology usage conditions;
- Sentence length, paragraphs, bullet points and information density;
- Formality, intimacy, and initiative;
- Commonly used connecting sentences, endings, and signatures;
- Expressions of time, amount, commitment and uncertainty;
- Common words, words to avoid, and tone differences for customers with different emotions.

Show the desensitization summary to the user and explicitly ask if they want to continue using it. `user_memory.md` is written with `status=approved` only after the user confirms "inherit" or gives a revision and confirms it. If the user does not agree, continue to modify or keep `not_reviewed`, and cannot be enabled silently.

## 4. Three-level classification processing plan

Process historical cases after tone confirmation:

1. Break down each customer problem into atomic requests.
2. It must be classified according to the first, second and third levels of `intent-taxonomy.csv`; one thread can produce multiple third-level classification records.
3. Summarize each third-level intention: applicable scenarios, verification information, processing steps, available solutions, permissions or upgrade points, commonly used phrases, avoided phrases, amount of historical evidence, and confidence level.
4. Only summarize the handling methods actually used by merchants, and do not mistakenly write customer requirements, AI drafts, unexecuted commitments, or single exceptions as routine practices.
5. The same three-level intention can be split according to the scene key. For example, "cancel before shipment" and "cannot be canceled directly after delivery to the carrier" cannot be combined.
6. Use the stable key `intent_id::scenario_key` to merge duplicate content; array fields are deduplicated, and the number of evidence is only increased for new observation IDs.
7. When the historical practice conflicts with the current policy or security access control, it will be recorded as `candidate` and marked with the conflict, and will not be used as a callable solution.

## 5. Continuous learning from manual modification of Draft

Only executed when learning is enabled:

1. After AI creates the draft, immediately use `scripts/draft_learning.py snapshot` to save the short-term desensitization baseline, draft ID, thread ID, latest customer message ID and third-level intent; the undesensitized text will not be saved.
2. Check the tracked draft and its thread first in each round. If the draft still exists, pull the current text and run `compare`; if it has been sent, use the text sent by the corresponding merchant in the thread for comparison.
3. Treat semantic changes only as learning signals. Ignore differences caused by Gmail's auto-formatting, citation history, signature position, whitespace, line breaks, and AI claims switches.
4. Divide the modifications into: tone preferences, structural preferences, fact corrections, treatment options changes, policy/authority changes, and this case only exceptions.
5. Tone and structure modifications can be incorporated into the style profile. Generalizable solution modifications are merged with scene keys by third-level intent. Instance values ​​such as order number, name, amount, address, etc. cannot be written.
6. Fact correction only prompts that there may be problems with the connector or matching, and does not write the corrected specific facts into global memory. Policy changes must be updated back to the official policy source, and rules cannot be established solely through Draft modifications.
7. Modifications involving illegality, discrimination, deception, product safety, privacy, chargebacks, over-authorization refunds or bypassing platform rules shall not be used as executable memory; write an internal warning and transfer it to manual review.
8. Pass the stable `observation_id` of the same modification to `user_memory.py merge`; repeated runs must not repeatedly add evidence.
9. Clear the short-term baseline of the Draft after the merge is successful. The baseline is retained for a configured maximum number of days and will be automatically cleared upon expiration.

## 6. Retrieve memory before replying

After matching items to a full order and before pulling campaigns and policies:

1. Read `user_memory.md`, first search by three-level intent ID, and then narrow the scope by scenario key, sales channel, product type and order status.
2. Only load entries with `status=approved` and consistent with the current case; `candidate`, `retired`, conflicting or low-confidence entries are only used for internal prompts.
3. Add the hit content to `user_memory_matches` of the case bundle, and record the memory key, applicable reason and conflict check result.
4. When there is no hit, directly use the Skill standard solution and do not invent user conventions.
5. Current order facts, activities, current policies, platform rules, legal requirements and security access control take priority. Memory only affects expression and preference selection among compliance options.

## 7. Memory update JSON structure

Write the desensitized updates into temporary JSON and then execute:

```bash
python3 scripts/user_memory.py merge --input /controlled temporary directory/memory-update.json
```

Minimal example:

```json
{
  "style_profile": {
    "status": "approved",
    "items": [
      {
        "key": "opening",
"summary": "Restate the specific problem first, and then express a brief apology",
        "source": "history_30d",
        "observation_id": "history-2026-07-opening-v1",
        "evidence_count": 12,
        "confidence": "high",
        "status": "approved"
      }
    ]
  },
  "handling_playbooks": [
    {
      "intent_id": "FULFILLMENT-DELAY-CARRIER",
"l1_name": "Logistics and Fulfillment",
"l2_name": "Transportation delay",
"l3_name": "Carrier transportation delay",
      "scenario_key": "carrier-delay-with-valid-scan",
"scenario": "There is a valid scan but the estimated delivery time has exceeded",
"handling_steps": ["Check the last scan", "Give the next checkpoint", "Upgrade carrier investigation after exceeding the threshold"],
"preferred_phrasing": ["I will continue to follow up with the next logistics update"],
"avoid_phrasing": ["Definitely arriving tomorrow"],
"constraints": ["Unconfirmed arrival dates by carriers are not guaranteed"],
      "source": "draft_edit",
      "observation_id": "draft-abc123-rev2",
      "evidence_count": 1,
      "confidence": "medium",
      "status": "approved"
    }
  ]
}
```

Update files are deleted immediately after use. Don't put original email fragments into update JSON.

