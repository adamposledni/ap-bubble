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

/** Stable identity of a job row: the job and its account. */
export function jobKey(jobName: string, scope: string | null): string {
  return `${jobName}|${scope ?? ''}`;
}

/** Whether the search text is in the job's label, raw name or account (case-insensitive). */
export function jobMatches(jobName: string, scope: string | null, search: string): boolean {
  const needle = search.trim().toLowerCase();
  if (!needle) return true;
  return [jobLabel(jobName), jobName, scopeLabel(scope)].some((text) =>
    text.toLowerCase().includes(needle),
  );
}
