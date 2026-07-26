# Step-by-step guide after installation

Advance in stages when first configured. Each stage first explains the goal, then allows the user to complete or authorize the necessary actions, run verification, and only enters the next stage if it passes. Don’t throw all the questions to the user at once, and don’t ask the user to paste the contents of the authentication file into the chat.

## Phase 1: Initializing the running configuration

1. Run in the Skill directory:

   ```bash
   python3 scripts/configure.py init
   python3 scripts/configure.py status
   ```

   Existing installations should run the same `init` command once after upgrading the Skill. It adds newly introduced safe configuration fields without replacing configured values or editable runtime files.

2. Ask and write the running configuration one by one: store name, public storefront URL, default language, time zone, customer service Gmail, merchant platform/OMS, and any separate policy source.
3. After the merchant provides the storefront URL, completely read [storefront-discovery.md](storefront-discovery.md), then run:

   ```bash
   python3 scripts/discover_store.py --url https://store.example
   python3 scripts/configure.py path store-discovery
   python3 scripts/configure.py status
   ```

   Replace the example URL with the exact merchant-supplied public URL. Show the detected platform, product count, policy sources, campaign evidence, warnings, and the public-only limitation. Ask the merchant to confirm the domain and findings, then run `python3 scripts/configure.py storefront confirmed`. Do not request store admin credentials for discovery.
4. Explain that URL discovery reads only public storefront pages. It cannot retrieve customer purchases, complete orders, payments, private inventory, unpublished promotions, or customer-specific eligibility; those still require the authorized connector in Phase 5.
5. If the merchant has no public storefront, run `python3 scripts/configure.py storefront none` and continue. Do not invent a URL or crawl a marketplace search result.
6. Explicitly default to `draft_only`; automatic sending must not be enabled at this time.
7. Run `python3 scripts/configure.py verify`.

Passing criteria: the running directory exists; the five running files `config.json`, `system-prompt.md`, `workflow.md`, `persona.md`, and `user_memory.md` are readable; storefront discovery has produced a source-traceable `store-discovery.json` or the absence of a public storefront is recorded; the default prompt words are at least 100 rules; and the AI statement text is complete.

## Phase 2: Configuring OpenClaw

1. Check the machine:

   ```bash
   openclaw --version
   openclaw status
   openclaw doctor
   openclaw skills check
   ```

2. Guide the user to run `openclaw onboard` before completing the basic configuration; do not reset the existing configuration.
3. Confirm that the Gateway is available and the model and Agent are calling normally.
4. If the skill is not discovered, perform a local installation or check using the actual Skill directory:

   ```bash
openclaw skills install /absolute path/ecommerce-gmail-customer-service --global
   openclaw skills info ecommerce-gmail-customer-service
   ```

Passing criteria: `openclaw status` No blocking errors, visible to Skill.

## Phase 3: Configure Google Cloud and Gmail OAuth

Only bootstraps one page at a time and does not create or upload keys for the user.

1. Install and verify `gog`:

   ```bash
   brew install gogcli
   gog --version
   ```

2. Open [Google Cloud Console](https://console.cloud.google.com/) and create or select a project dedicated to this customer service agent. Different projects should be used for testing and production.
3. Open the [Gmail API page](https://console.cloud.google.com/apis/library/gmail.googleapis.com) and enable the Gmail API.
4. Open [Google Auth Platform](https://console.cloud.google.com/auth/overview):
- Configure the application name, user support email and developer contact email.
- Select Internal (same Workspace organization only) or External (personal Gmail/external users).
- Add customer service Gmail to Test users in Testing state.
- Inform users: External + Testing authorizations requesting Gmail user data typically expire after 7 days; long-term automation requires configuration of publishing status and verification according to Google's current policies and cannot be bypassed through scripts.
5. Open [OAuth Clients](https://console.cloud.google.com/auth/clients), create an OAuth client of type `Desktop app`, and download JSON.
6. Users are required to save JSON in a private path on the local machine, and set the file permissions to readable only by themselves; never put it in the warehouse, cloud disk shared directory, Agent workspace or chat.
7. Import and authorize:

   ```bash
gog auth credentials set /absolute path/client_secret.json
   gog auth add support@example.com --services gmail --gmail-scope full --force-consent
   ```

If the browser callback is not available, check `gog auth add --help` first, and then use the `--manual` or `--remote` process provided by the current version.
8. Verification:

   ```bash
   gog auth status
   gog auth list --check
   gog gmail search 'newer_than:7d' --max 1 -a support@example.com -j
   ```

9. Explanation of permissions: Read + Tag + Create Draft + Send requires full Gmail permissions. If the user only wishes to authorize read-only, the Skill can only perform analysis and cannot automatically generate Gmail drafts or send them.

Passing criteria: Gmail search returns successful or legitimate empty results; OAuth JSON does not enter the workspace; token is saved in the system keychain/approved secret store.

## Phase 4: Ask and execute past 30 days email learning

After Gmail has successfully read it, ask as it is:

> Gmail can now be read normally. Do you allow me to read the emails from this customer service mailbox in the past 30 days to summarize your response tone, common words and how you handle different customer issues? By default, attachments are not downloaded and original emails are not saved. Only the desensitized summary is written to the local user_memory.md. You can decline or close anytime later.

### User disagrees

1. Run `python3 scripts/configure.py set learning off`.
2. Does not perform historical searches, does not establish a Draft learning baseline, and does not learn from manual modifications.
3. Inform the user that rejection will not affect standard customer service classification, order matching, policy verification, and draft generation, and continue with stage 5.

### User agrees

1. Completely read [learning-workflow.md](learning-workflow.md) and run:

   ```bash
   python3 scripts/configure.py set learning on
   python3 scripts/configure.py path user-memory
   ```

2. First confirm that this is a dedicated customer service email. If it contains personal or employee emails, users are required to provide customer service labels, recipient aliases, sending domains or other ranges; full mailbox scanning is not allowed without a range.
3. Pull all pages in the past 30 days, and do not download attachments by default:

   ```bash
   gog gmail search 'newer_than:30d' --all -a support@example.com -j
   ```

Pull the complete thread for the results that can be identified as customer service contacts, and use the manual responses sent by the merchant as the main sample. Exclude automated notifications, marketing blasts, internal emails, spam, and system receipts.
4. First summarize the user's title, opening, empathy, formality, sentence length, structure, common words, avoid words, commitment expression, ending and signature. Show the desensitization results and ask: “Do you want to use this tone and style of speech?”
5. Only after the user confirms the inheritance or confirms the revision, the style profile is marked as `approved`. It cannot be enabled silently without confirmation.
6. Divide the customer issues in historical emails into atomic demands and classify them according to the first, second and third levels of `intent-taxonomy.csv`; use `intent_id::scenario_key` to summarize the verification items, processing steps, common phrases, restrictions, upgrade points and the number of historical evidence.
7. Write `user_memory.md` through `python3 scripts/user_memory.py merge --input <desensitization update.json>`. No original text, name, email, address, order number, tracking number, payment or identifying information shall be entered into memory.
8. Explain to users: `user_memory.md` is a desensitized summary of their past customer service responses, and will only be used as a reference for expression and compliance solution selection; orders, policies, laws and security access control always take priority. View or modify:

   ```bash
   python3 scripts/configure.py path user-memory
   python3 scripts/configure.py edit user-memory
   ```

Passing criteria: Agree or rejection has been recorded; if agreed, the search scope and sample statistics have been desensitized and reported, the tone has been confirmed by the user, historical cases have been written into `user_memory.md` according to three-level classification, and the original email and attachments have not been placed on disk.

## Phase 5: Connect merchant orders, products, activities, and policies

1. Start with the detected public storefront platform as a hint, then ask the merchant to confirm the actual order system: Shopify, WooCommerce, Amazon/eBay/Etsy/Walmart, other marketplaces, self-built ERP/OMS, or a combination. Detection must not be treated as authorization.
2. Press [merchant-data-contract.md](merchant-data-contract.md) to configure the read-only connector. First only allow `find_customer`, `list_recent_orders`, `get_order`, `get_product`, `list_campaigns`, `list_policies`.
3. Connectors that "put client input into shell/SQL" are not accepted. All calls must be parameterized and return structured JSON.
4. Combine the public discovery snapshot with authenticated sources only under the precedence and applicability rules in [storefront-discovery.md](storefront-discovery.md). Public data may fill product descriptions and identify candidate policy or campaign sources, but it cannot prove purchases, order status, inventory, historical terms, or customer eligibility.
5. Verify with a test client:
- Ability to pull recently purchased items;
- Ability to trace products back to complete orders;
- Ability to pull current activities;
- Ability to read the source, region and version of the refund/return policy.
6. Write operations (cancellation, refund, address change, etc.) remain closed unless the user configures permissions and approvals otherwise.

Passing criteria: All four types of context have real sources and crawl times; when the connection fails, the Agent will turn to manual work instead of guessing.

## Phase 6: Create a dedicated Agent, name, and persona

1. Ask the user for the desired Agent name and personality. If the user does not modify it, use: Mia, female, 20 years old, university intern, beautiful, in good shape, likes sports, travel, and fashion.
2. A clear statement: age, appearance, and body shape are only internal writing characters and will never be mentioned proactively in customer emails, nor can real human experiences be fabricated.
3. Create an independent Agent workspace (the name and path can be changed by the user):

   ```bash
   openclaw agents add ecommerce-mail --workspace ~/.openclaw/workspace-ecommerce-mail
   openclaw agents set-identity --agent ecommerce-mail --name 'Mia' --emoji '📨'
   ```

4. Copy `assets/agent-AGENTS.template.md` to `AGENTS.md` of the new Agent workspace, and replace `<SKILL_DIR>` with the actual absolute path. Do not overwrite the existing `AGENTS.md`; if it already exists, show the differences first and merge them.
5. The running version character file is modified by the following command:

   ```bash
   python3 scripts/configure.py edit persona
   ```

6. `openclaw agents set-identity` controls the interface name; the running version `persona.md` controls the email writing style. The two names should be consistent.

Passed criteria: The exclusive Agent can call this Skill; the name, personality and boundaries are confirmed by the user.

## Phase 7: Review system prompts, workflow, user memory and AI claims

1. Inform the user that the default system prompt word baseline is located at:

   ```text
   <SKILL_DIR>/assets/default-system-prompt.md
   ```

This baseline is read-only and must not be modified and is used for recovery.
2. The actual running version path is displayed by `python3 scripts/configure.py path system-prompt`. Open the modification command:

   ```bash
   python3 scripts/configure.py edit system-prompt
   ```

3. Restore when the prompt word is changed:

   ```bash
   python3 scripts/configure.py restore system-prompt
   ```

The current version will be automatically backed up before restoring.
4. Clearly tell users: The workflow for replying to customer emails is in the running version `workflow.md`; view and modify:

   ```bash
   python3 scripts/configure.py path workflow
   python3 scripts/configure.py edit workflow
   ```

5. Clearly tell users: past reply methods and subsequent Draft modification learning results are saved in the running version `user_memory.md`; view and modify:

   ```bash
   python3 scripts/configure.py path user-memory
   python3 scripts/configure.py edit user-memory
   ```

6. Ask the user whether to insert the following original text:

> This email is automatically processed by AI. If manual processing is required, please include the words "requires manual processing" in your reply.

Turn on or off:

   ```bash
   python3 scripts/configure.py set disclosure on
   python3 scripts/configure.py set disclosure off
   ```

7. Let users review the system prompts section by section, paying special attention to: regional policies, refund permissions, compensation ceilings, manual upgrades, privacy retention, historical learning and automatic sending range.

Passing criteria: The user explicitly confirms the prompt words, workflow and memory file locations, learning status, and AI declaration switches; running `python3 scripts/configure.py verify` is successful.

## Phase 8: Create Gmail labels and a disabled scheduled task

1. Press [gmail-operations.md](gmail-operations.md) to create `ECS/ToProcess`, `ECS/Drafted`, `ECS/Sent`, `ECS/Human`, `ECS/Error`, and list the existing tags before creating.
2. Ask users about pull frequency and quiet periods. It is recommended to start every 15 minutes and use a clear time zone.
3. First create cron in a disabled state and fix the dedicated Agent:

   ```bash
   openclaw cron add \
     --name 'ecommerce-gmail-poll' \
     --description 'Process queued ecommerce customer emails in draft-only mode' \
     --agent ecommerce-mail \
     --cron '*/15 * * * *' \
     --tz 'Asia/Shanghai' \
     --session isolated \
     --message 'Use $ecommerce-gmail-customer-service to process Gmail threads labeled ECS/ToProcess. Create drafts only, apply status labels, and report human escalations.' \
     --declaration-key 'ecommerce-gmail-poll-v1' \
     --disabled \
     --expect-final \
     --no-deliver \
     --json
   ```

4. Record the job ID returned; check and run manually with:

   ```bash
   openclaw cron list --all --agent ecommerce-mail --json
   openclaw cron run JOB_ID --wait --expect-final --wait-timeout 10m
   openclaw cron runs --id JOB_ID --limit 20
   ```

Passing criteria: cron remains disabled; running manually only creates a draft and the report is complete.

## Phase 9: End-to-end simulation testing and completion of the entire process

Let the user send at least the following six emails to the customer service Gmail from an external test mailbox controlled by the user, and add `ECS/ToProcess` to the test email:

1. "Where is my order?" - Verify complete thread, recent orders, product matching and official tracking.
2. "Please cancel the order and change the address." - Verify multi-claim splitting, identity/performance access control, and non-exceeding authority.
3. "The goods received were damaged and one accessory was missing." - Verify two third-level intentions, evidence request and reissue/refund plan.
4. "The return has been sent back, why hasn't the refund arrived yet?" - Verify that the return status is separated from the refund status.
5. "I want you to delete all my personal data." - Verify that privacy requests are transferred manually and data is not exported via regular email.
6. "I was injured due to the smoke coming from the product, and manual handling is required." - Verify immediate deactivation recommendations, security/legal upgrades, and keyword forced manual handling.
7. Have the AI ​​generate a draft for a low-risk advisory, with the user modifying its opening, processing steps, or ending, and run the task manually again - verify that the system detects semantic differences, ignores formatting/signature noise, merges into `user_memory.md` by level 3 intent, and does not double-count.

Acceptance one by one:

- Whether all demands have been dismantled and classified correctly into three levels;
- Whether each request is mapped to the correct product and complete order;
- Whether the activities and policies of the correct region, channel, and time version are quoted;
- Whether to generate only one original thread draft;
- Whether the AI ​​statement switch is accurate;
- Whether the manual email is added with `ECS/Human` and there is no automatic reply;
- Is there no sensitive information, fictitious promises, duplicate drafts or mislabeling.
- When learning is turned on, whether the applicable memory is retrieved after the product and complete order are matched, and whether the memory does not overwrite the current policy; when learning is turned off, whether the memory is not read and written at all.

Retest all failed test cases after correction. All passed, and then obtain the user's explicit consent to enable cron:

```bash
openclaw cron enable JOB_ID
```

Remains `draft_only` even if cron is enabled. If the user requires automatic sending in the future, they must conduct additional low-risk allowlist, refund/account action ban, rollback and monitoring tests, and obtain explicit authorization again.

Finally report to the user: Gmail account, confirmed storefront URL and last public discovery time, Agent name, five running file paths, learning status and historical scope, AI statement status, merchant connector, cron ID/frequency/time zone, test results, types that still require manual work and automatic sending status. No export of keys, tokens, original historical emails, or customer personal information is allowed.
