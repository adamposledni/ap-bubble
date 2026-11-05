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
- [ ] Schedule ingest jobs (Windows Task Scheduler).
