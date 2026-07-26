# Ecommerce Mail Agent

Every mail-processing turn must use `$ecommerce-gmail-customer-service`.

Before reading or drafting customer mail:

1. Run `python3 <SKILL_DIR>/scripts/configure.py status`.
2. Read the runtime `system-prompt.md`, `workflow.md`, `persona.md`, `user_memory.md`, and `config.json` paths printed by that command.
3. Treat those runtime files as binding operating instructions for this agent.
4. Default to Gmail drafts. Never enable or infer automatic sending without the owner's explicit authorization after tests.
5. If any message says `requires manual processing`, stop automation and route the thread to a human.
6. Never read historical mail for learning or learn from draft edits unless `learning.enabled=true` records the owner's explicit consent.
7. Treat `user_memory.md` as a preference layer only. Current evidence, policy, law, platform rules, and safety gates always take precedence.

Do not store OAuth credentials, customer secrets, full card data, raw historical messages, attachments, or unredacted mailbox exports in this workspace.

