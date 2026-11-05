# TODO

## Ingest

- [ ] Google Calendar: load history before 2026-01-01. Move `SYNC_FROM` in
      `apps/ap-bubble-ingest/src/bubble_ingest/google/calendar/sync.py` back (or drop the limit),
      then delete the `google_calendar` rows in `lm_sync_cursors` to force a full load.
- [ ] Google Calendar: calendars removed from the calendar list keep their L0 items; flag them deleted.
- [ ] Recurring events sit in L0 as series + exceptions; expand them into occurrences where
      dashboard / MCP queries need them.
- [ ] Google Tasks: task lists deleted in Google keep their L0 items; flag them deleted.
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
- [ ] Schedule ingest jobs (Windows Task Scheduler).
