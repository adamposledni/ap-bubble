// JSON shapes of the API (apps/ap-bubble-api/src/bubble_api/models.py).

/** Whether an item comes from a work or a personal account. */
export type Context = 'work' | 'personal';

export interface AgendaEvent {
  key: string;
  calendar: string | null;
  context: Context;
  title: string | null;
  start: string; // UTC timestamp, or YYYY-MM-DD for all-day events
  end: string; // exclusive
  allDay: boolean;
  location: string | null;
  recurring: boolean;
}

export interface OpenTask {
  id: number;
  listName: string | null;
  context: Context;
  title: string | null;
  notes: string | null;
  due: string | null; // YYYY-MM-DD
  subtasks: OpenTask[];
}

export type RunStatus = 'running' | 'succeeded' | 'failed';

export interface JobStatus {
  jobName: string;
  scope: string | null; // e.g. account key 'google:me@gmail.com'
  lastStatus: RunStatus;
  lastStartedAt: string;
  lastSuccessAt: string | null;
  lastError: string | null;
  itemsInL0: number | null;
  stale: boolean;
}

export interface JobRun {
  id: number;
  jobName: string;
  scope: string | null;
  status: RunStatus;
  startedAt: string;
  durationSeconds: number | null;
  itemsProcessed: number;
  error: string | null;
}

export interface Monitor {
  jobs: JobStatus[];
  runs: JobRun[];
  queue: Partial<Record<InputStatus, number>>;
}

export type InputStatus = 'queued' | 'processing' | 'done' | 'failed';

export interface InputFile {
  id: number;
  name: string;
  mediaType: string | null;
  sizeBytes: number;
}

export interface InputItem {
  id: number;
  text: string | null;
  status: InputStatus;
  error: string | null;
  createdAt: string;
  processedAt: string | null;
  files: InputFile[];
}
