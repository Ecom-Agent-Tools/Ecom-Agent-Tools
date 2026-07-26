# Gmail and gog operating instructions

The following commands are written in the natively validated `gog 0.12.0` syntax. After upgrading, run `gog --help`, `gog schema gmail` and each subcommand `--help` to check, and do not blindly use old commands.

## Installation and authentication check

```bash
brew install gogcli
gog --version
gog auth status
gog auth list --check
```

Google Cloud OAuth client import with Gmail authorization:

```bash
gog auth credentials set /absolute path/client_secret.json
gog auth add support@example.com --services gmail --gmail-scope full --force-consent
gog auth list --check
gog gmail search 'newer_than:7d' --max 1 -a support@example.com -j
```

`gmail.readonly` can only read, but cannot create drafts, add tags or send; this Skill requires full Gmail permissions. OAuth JSON, refresh tokens, and keychain passwords must not enter the repository, logs, or emails.

## Tag initialization

```bash
gog gmail labels list -a support@example.com
gog gmail labels create 'ECS/ToProcess' -a support@example.com
gog gmail labels create 'ECS/Drafted' -a support@example.com
gog gmail labels create 'ECS/Sent' -a support@example.com
gog gmail labels create 'ECS/Human' -a support@example.com
gog gmail labels create 'ECS/Error' -a support@example.com
```

List tags before creating to avoid duplication.

## Pull queue and complete thread

```bash
gog gmail search 'label:ECS/ToProcess is:unread newer_than:30d' --max 20 -a support@example.com -j
gog gmail thread get THREAD_ID --full -a support@example.com -j
```

Mandatory rule: Processed by thread; single `gmail get` cannot be used instead of a full thread. Do not automatically download unknown attachments; use quarantine directories when attachments are truly needed and keep them read-only for analysis.

## First 30 Days of History Study

Only runs if the user explicitly agrees and `learning.enabled=true` is set. The dedicated customer service mailbox can pull all pages in the past 30 days:

```bash
gog gmail search 'newer_than:30d' --all -a support@example.com -j
```

If the email is not a dedicated customer service email, the query must first be narrowed to the customer service label, recipient alias or sending domain confirmed by the user. Use `gog gmail thread get THREAD_ID --full` to read the sending and receiving context for candidate results; do not download attachments. The analysis focuses on customer service threads containing manual responses from merchants, excluding automatic notifications, marketing mass mailings, internal emails, spam emails, and system receipts. Search JSON, thread text, or full mailbox exports must not be saved to the Skill, Agent workspace, or `user_memory.md`.

## Draft Idempotent

First check if thread already has a draft:

```bash
gog gmail drafts list -a support@example.com -j
```

When thread has a new customer email, delete the old draft and recreate it:

```bash
gog gmail drafts delete DRAFT_ID -a support@example.com -y
gog gmail drafts create \
  --to='customer@example.com' \
  --subject='Re: Existing subject' \
  --reply-to-message-id=LATEST_MESSAGE_ID \
--body-file=/absolute path/reply.txt \
  -a support@example.com -j
```

Prefer `--body-file` to avoid multi-line body text being destroyed by shell escaping. Temporary text files are only placed in the permission-controlled running directory and deleted according to retention rules.

## Manually modify the learning detection of Draft

When learning is enabled, the desensitization baseline is saved immediately after the draft is successfully created:

```bash
python3 scripts/draft_learning.py snapshot \
  --draft-id DRAFT_ID \
  --thread-id THREAD_ID \
  --message-id LATEST_MESSAGE_ID \
  --intent FULFILLMENT-DELAY-CARRIER \
--body-file/controlled temporary directory/reply.txt
```

In subsequent rounds, use `gog gmail drafts get DRAFT_ID -j` to obtain the current draft; if the draft has been sent, obtain the corresponding text sent by the merchant from the complete thread. Write the text to a temporary file with controlled permissions, and then compare:

```bash
python3 scripts/draft_learning.py compare \
  --draft-id DRAFT_ID \
--body-file/controlled temporary directory/current-reply.txt
```

The comparison output has undergone basic desensitization, but is still only available for native analysis. AI generates and merges desensitized memory updates according to [learning-workflow.md](learning-workflow.md), and then executes:

```bash
python3 scripts/draft_learning.py finalize --draft-id DRAFT_ID
python3 scripts/draft_learning.py purge
```

Baselines may not be established, compared, or retained while learning is off. Pure formatting, citation history, signature position, or AI claim changes should not be relied upon as user preferences.

## Tags and status

```bash
gog gmail messages modify MESSAGE_ID --add='ECS/Drafted' --remove='ECS/Error' -a support@example.com -y
gog gmail messages modify MESSAGE_ID --add='ECS/Human' -a support@example.com -y
gog gmail mark-read MESSAGE_ID -a support@example.com -y
```

Do not mark unresolved or manually escalated emails as read just to clear your inbox. Record thread, message and target labels before batch modification.

## Send access control

The send command is not run by default. Only used if both configuration and case allow it:

```bash
gog gmail drafts send DRAFT_ID -a support@example.com
```

Before sending, recheck the recipient, thread, latest message, all requests, order, amount, policy, link, attachment, AI statement and manual access control. Any uncertain items return to draft mode.

## Network retry

Only retry for timeout, connection reset, temporary proxy or 5xx, up to 3 times, wait 5, 10, 20 seconds. 401/403, scope, data validation, policy violation and parameter errors stop immediately and write `ECS/Error`.

