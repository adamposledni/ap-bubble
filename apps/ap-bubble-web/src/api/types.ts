// JSON shapes of the API (apps/ap-bubble-api/src/bubble_api/models.py).

export interface AgendaEvent {
  key: string;
  calendar: string | null;
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
  title: string | null;
  notes: string | null;
  due: string | null; // YYYY-MM-DD
  subtasks: OpenTask[];
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
