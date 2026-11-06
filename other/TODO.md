# TODO

## Ingest

- [ ] Google Calendar: load history before 2026-01-01. Move `SYNC_FROM` in
      `apps/ap-bubble-ingest/src/bubble_ingest/google/calendar/sync.py` back (or drop the limit),
      then delete the `google_calendar` rows in `lm_sync_cursors` to force a full load.
- [ ] Google Calendar / Tasks, Outlook calendar, To Do: a removed calendar or task list is flagged
      deleted (kind `calendar` / `tasklist`), but its events / tasks are not; readers filter by live
      containers. Flag them too if other readers (curator, MCP) need it.
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
- [ ] Outlook calendar: load history before 2026-01-01 (move `SYNC_FROM` in
      `apps/ap-bubble-ingest/src/bubble_ingest/microsoft/calendar/sync.py`, then delete the
      `outlook_calendar` rows in `lm_sync_cursors`).
- [ ] Outlook calendar: the window ends at `SYNC_UNTIL` = 2028-01-01 (the delta link encodes the
      window), so the look-ahead shrinks; move it forward before late 2027, then delete the
      `outlook_calendar` rows in `lm_sync_cursors`.
- [ ] Outlook calendar: the 14 calendars shared with me by colleagues are skipped (only own ones
      sync); add an opt-in list if some should show in the agenda (they would load fully each run).
- [ ] Outlook calendar: non-default calendars load fully every run (v1.0 documents calendarView delta
      only for the default calendar); switch once v1.0 documents per-calendar delta.
- [ ] Outlook calendar: delta also returns series masters (kept in L0, left out of the agenda) and
      `@removed` entries for events outside the window; unknown ids among those become deleted rows.
- [ ] Outlook mail: load mail before 2026-01-01 (move `SYNC_FROM` in
      `apps/ap-bubble-ingest/src/bubble_ingest/microsoft/mail/scope.py`, then delete the
      `outlook_mail` rows in `lm_sync_cursors`).
- [ ] Outlook mail: Graph caps a filtered first load at 5,000 messages per folder; a folder that
      reaches it is loaded unfiltered (its whole history is downloaded once, older mail dropped).
- [ ] Outlook mail: attachments are not downloaded (only `hasAttachments`); `uniqueBody` (only the
      new part of a reply) could save curator tokens; archive and shared mailboxes are not ingested.
- [ ] Planner: task details (description, checklist, references) need one call per task and are not
      ingested, so open tasks show no notes for Planner. Every run is a full load (no v1.0 delta).
- [ ] To Do: checklist items and linked resources (e.g. the mail behind a Flagged email task) are not
      ingested.
- [ ] Microsoft due dates are converted to this PC's time zone at ingest
      (`bubble_ingest/microsoft/due_dates.py`); a zone change does not recompute stored rows.
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

- [ ] Monitor follow-ups (the basic page exists): show the failed/stale banner on the Overview too,
      detect runs stuck in `running` (a killed process never finishes its row), add curator runs and
      executed actions once they exist.
