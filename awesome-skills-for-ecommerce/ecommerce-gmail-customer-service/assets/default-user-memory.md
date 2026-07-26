# User customer service memory

> This file saves the email writing preferences confirmed by the user, as well as the classification processing practices summarized from historical customer service responses and manual modifications to the Draft. It is not a source of fact for orders, policies, laws or Platform rules. Current evidence and mandatory rules always take precedence.

## Instructions for use

- Learning is not enabled by default; historical emails are read or Draft modifications are analyzed only with explicit user consent.
- Only desensitized, generalizable summaries are saved, and original emails, attachments or customer personal information are not saved.
- You can run `python3 scripts/configure.py edit user-memory` to view or modify this file.
- You can run `python3 scripts/configure.py set learning off` to stop subsequent reading and writing; deleting existing memory requires explicit user request.

## Current status

- History learning: not started yet
- Historical range: past 30 days
- Tone plan: to be summarized and confirmed
- Classification solutions: 0 items
- Last updated: None

## Confirmed tone and diction

Not yet.

## Treatment plans organized according to three levels of classification

Not yet.

<!-- ECS_MEMORY_JSON_BEGIN -->
```json
{
  "schema_version": 1,
  "history_learning": {
    "status": "not_started",
    "window_days": 30,
    "approved_at": null,
    "last_scan_at": null,
    "source_threads": 0
  },
  "style_profile": {
    "status": "not_reviewed",
    "items": []
  },
  "handling_playbooks": [],
  "updated_at": null
}
```
<!-- ECS_MEMORY_JSON_END -->

