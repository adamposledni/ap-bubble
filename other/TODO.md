# TODO

## Ingest

- [ ] Google Calendar: load history before 2026-01-01. Move `SYNC_FROM` in
      `apps/ap-bubble-ingest/src/bubble_ingest/google/calendar/sync.py` back (or drop the limit),
      then delete the `google_calendar` rows in `lm_sync_cursors` to force a full load.
- [ ] Google Calendar / Tasks: a removed calendar or task list is flagged deleted (kind `calendar` /
      `tasklist`), but its events / tasks are not; readers filter by live containers. Flag them too
      if other readers (curator, MCP) need it.
- [ ] Recurring events sit in L0 as series + exceptions; expand them into occurrences where
      dashboard / MCP queries need them.
- [ ] Google Tasks: incremental sync (`updatedMin`) never sees tasks that vanish without a deleted
      flag (e.g. moved to another list, or purged while sync was paused); add a periodic full load
      (delete the `google_tasks` rows in `lm_sync_cursors`).
- [ ] Google Contacts: changing the field masks in
      `apps/ap-bubble-ingest/src/bubble_ingest/google/contacts/api.py` invalidates the stored sync
      tokens; delete the `google_contacts` rows in `lm_sync_cursors` to force a full load.
- [ ] Google Contacts: contact groups are not ingested (memberships hold only group resource names).
- [ ] Gmail: load mail before 2026-01-01. Move `SYNC_FROM` in
      `apps/ap-bubble-ingest/src/bubble_ingest/google/gmail/scope.py` back (or drop the limit),
      then delete the `gmail` row in `lm_sync_cursors` to force a full load.
- [ ] Gmail: quota is ~100 full messages/min (measured); label-only changes could use
      format=minimal and patch labelIds instead of a full refetch.
- [ ] Gmail: attachments are not downloaded; attachmentId is not stored (Gmail changes it on every
      fetch), so a downloader fetches the message again and finds the part by partId.
- [ ] Gmail: drafts are ingested like other mail; each draft save is a new message (old one
      deleted). Exclude drafts if that churn bothers the curator.
- [ ] Check performance improvements to ingestion: multiple async/concurrent requests (per container,
      per account, per source). Mind per-user quotas: Gmail measured ~100 full messages/min, and a
      run right after a full load waits out the rate limit (incremental with 0 changes took 65 s).
- [ ] OneNote ingest (postponed 2026-11-06; `Notes.Read` is already granted): sections as containers,
      page metadata listed every run, page content (HTML) fetched only for new or changed pages.
- [ ] Schedule ingest jobs (Windows Task Scheduler).

## Web UI

- [ ] Run the web app without dev servers: build the UI and serve it from the API (one process),
      started at logon (e.g. Task Scheduler) instead of `tools/web.ps1`.
- [ ] Overview reads L0 directly; switch it to the curated layer (L2) once it exists.

- [ ] Monitor / audit page: job runs from `lm_job_runs` (status, duration, errors, items processed),
      data freshness per source and account, warning banner when ingest or curator failed or data is
      stale (REQUIREMENTS §8.1 Audit).
