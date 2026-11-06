// Display names for jobs and their scopes.

const SOURCE_NAMES: Record<string, string> = {
  google_calendar: 'Google Calendar',
  google_tasks: 'Google Tasks',
  google_contacts: 'Google Contacts',
  gmail: 'Gmail',
  outlook_calendar: 'Outlook calendar',
  outlook_mail: 'Outlook mail',
  planner: 'Planner',
  microsoft_todo: 'To Do',
  teams_chats: 'Teams chats',
};

const JOB_NAMES: Record<string, string> = {
  'curator.run': 'Curator',
  'curator.dry_run': 'Curator (dry run)',
};

/** 'ingest.google_calendar' → 'Google Calendar'; unknown jobs keep their name. */
export function jobLabel(jobName: string): string {
  const source = jobName.replace(/^ingest\./, '');
  return JOB_NAMES[jobName] ?? SOURCE_NAMES[source] ?? jobName;
}

/** 'google:me@gmail.com' → 'me@gmail.com'. */
export function scopeLabel(scope: string | null): string {
  return scope ? scope.slice(scope.indexOf(':') + 1) : '—';
}
