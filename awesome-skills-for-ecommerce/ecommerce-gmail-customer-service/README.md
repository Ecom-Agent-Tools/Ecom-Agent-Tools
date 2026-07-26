# E-commerce Gmail Customer Service

An OpenClaw Skill for handling e-commerce customer-service email safely in Gmail.

It turns incoming customer threads into auditable reply drafts: it separates multiple requests, classifies each one with a three-level intent taxonomy, matches the request to products and complete orders, checks current campaigns and policies, and writes one clear reply for the thread.

## What it does

- Handles pre-sale questions, order changes, shipping, damaged or missing items, returns, refunds, warranties, subscriptions, privacy requests, complaints, and more.
- Matches each request to the relevant product and complete order instead of guessing.
- Uses merchant policies and current campaign information when preparing a response.
- Lets the merchant enter one public storefront URL during setup, then safely discovers public product data, likely campaign pages, and policy sources with timestamps and provenance.
- Creates Gmail drafts by default; sending is disabled until explicitly configured and tested.
- Escalates high-risk cases such as safety incidents, legal complaints, chargebacks, privacy requests, fraud, and requests containing `requires manual processing`.
- Can optionally learn approved writing preferences and reusable handling patterns from the previous 30 days of a dedicated support mailbox. This requires explicit user consent and stores only redacted summaries in `user_memory.md`.

## Prerequisites

- OpenClaw installed and working.
- A dedicated Gmail support inbox.
- Google Cloud OAuth credentials with the Gmail API enabled.
- `gogcli` installed for Gmail access.
- A public storefront URL, when the merchant has one.
- Read-only authenticated connections to the store or OMS for customer purchases, complete orders, private inventory, and customer-specific eligibility.

## Install

Clone this repository, then install the Skill from the repository checkout:

```bash
git clone https://github.com/Ecom-Agent-Tools/Ecom-Agent-Tools.git
cd Ecom-Agent-Tools
openclaw skills install ./awesome-skills-for-ecommerce/ecommerce-gmail-customer-service --global
openclaw skills info ecommerce-gmail-customer-service
```

If OpenClaw is not configured yet, run `openclaw onboard` first. Do not place OAuth client files, tokens, or other secrets in this repository.

## First-time setup

Start the guided setup by asking your OpenClaw agent to configure the e-commerce Gmail customer-service Skill. The complete walkthrough is in [references/onboarding.md](references/onboarding.md).

The setup guides you through:

1. Creating the runtime configuration.
2. Entering the storefront URL and reviewing automatically discovered public products, campaigns, and policy sources.
3. Enabling the Gmail API and completing Gmail OAuth.
4. Connecting authenticated read-only order and private merchant data sources.
5. Naming the customer-service Agent and setting its persona.
6. Reviewing the system prompt, workflow, and optional AI disclosure.
7. Optionally approving 30-day historical-email learning.
8. Creating a disabled scheduled task and running end-to-end draft-only tests.

From the Skill directory, initialize and inspect the runtime files:

```bash
python3 scripts/configure.py init
python3 scripts/discover_store.py --url https://store.example
python3 scripts/configure.py storefront confirmed
python3 scripts/configure.py status
python3 scripts/configure.py verify
```

## Everyday use

Label customer email threads with `ECS/ToProcess`, then ask the Agent to process them with this Skill. The default result is a Gmail draft in the original thread.

Useful commands:

```bash
python3 scripts/configure.py edit system-prompt
python3 scripts/configure.py edit workflow
python3 scripts/configure.py edit persona
python3 scripts/configure.py path user-memory
python3 scripts/configure.py set disclosure on
python3 scripts/configure.py set learning on
```

The optional AI disclosure is:

> This email is automatically processed by AI. If manual processing is required, please include the words "requires manual processing" in your reply.

Customers can request escalation by including `requires manual processing` anywhere in their reply.

## Safety model

This Skill starts in `draft_only` mode. It does not guess order facts, inventory, shipping status, refunds, or policy eligibility. It also never treats historical writing preferences as a replacement for current order data, policies, platform rules, or applicable law.

Storefront discovery reads only public pages, respects `robots.txt`, rejects private-network and cross-host access, and uses strict page and response limits. Public storefront content is candidate evidence only; complete orders and customer-specific decisions still require an authorized commerce connector.

Review the generated drafts before sending, especially during initial deployment and after changing a connector, system prompt, or workflow.

## Project files

- [SKILL.md](SKILL.md) — operational instructions and guardrails.
- [references/onboarding.md](references/onboarding.md) — guided setup.
- [references/storefront-discovery.md](references/storefront-discovery.md) — safe public storefront discovery and evidence rules.
- [references/intent-taxonomy.csv](references/intent-taxonomy.csv) — three-level customer-intent taxonomy.
- [references/reply-playbooks.md](references/reply-playbooks.md) — reusable reply approaches.
- [assets/default-system-prompt.md](assets/default-system-prompt.md) — immutable baseline safety prompt.
