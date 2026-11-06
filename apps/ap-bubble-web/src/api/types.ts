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
  finishedAt: string | null;
  durationSeconds: number | null;
  itemsProcessed: number;
  error: string | null;
  dryRun: boolean; // a curator run that only wrote its batch files
}

export interface RunningJob {
  run: JobRun;
  batchCurrent: number | null; // curator only
  batchTotal: number | null;
}

export type BatchStatus = 'done' | 'failed' | 'running' | 'pending' | 'not_sent';

export interface Batch {
  name: string;
  status: BatchStatus;
  summary: string | null;
  numTurns: number | null;
  durationSeconds: number | null;
  costUsd: number | null;
}

export interface RunDetail {
  run: JobRun;
  batches: Batch[]; // curator runs only
}

export interface Monitor {
  jobs: JobStatus[];
  runs: JobRun[]; // the last 7 days
  running: RunningJob[];
  queue: Partial<Record<InputStatus, number>>;
  changesWaiting: number; // L0 rows past the curator cursor
}

export interface Question {
  id: string;
  text: string;
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

export type KnowledgeFolder = 'people' | 'places' | 'topics' | 'me';

/** A piece of a search snippet; match marks the words that matched the query. */
export interface SnippetPart {
  text: string;
  match: boolean;
}

export interface KnowledgeHit {
  folder: KnowledgeFolder;
  slug: string;
  name: string;
  tags: string[];
  updated: string | null; // YYYY-MM-DD
  snippet: SnippetPart[];
}

export interface KnowledgeSearch {
  total: number; // all matches; hits holds at most the limit
  hits: KnowledgeHit[];
}

export interface KnowledgeMeta {
  name: string;
  aliases: string[];
  emails: string[];
  phones: string[];
  tags: string[];
  updated: string | null; // YYYY-MM-DD
}

export interface KnowledgeRef {
  folder: KnowledgeFolder;
  slug: string;
  name: string;
}

export interface KnowledgeDoc {
  folder: KnowledgeFolder;
  slug: string;
  meta: KnowledgeMeta;
  body: string; // markdown
  backlinks: KnowledgeRef[];
}
