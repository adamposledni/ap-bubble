// Sources a knowledge file cites: an L1 input (input:7), an L0 item (l0:123) or a range (l0:504–519).

export type SourceRef =
  | { type: 'input'; id: number }
  | { type: 'item'; id: number }
  | { type: 'items'; from: number; to: number };

const SOURCE = /^(input|l0):(\d+)(?:[–-](\d+))?$/;

/** The source a citation such as 'l0:504–519' points to; undefined for input ranges and anything else. */
export function parseSourceRef(text: string): SourceRef | undefined {
  const match = SOURCE.exec(text);
  if (!match) return undefined;
  const [, layer, first, last] = match;
  if (layer === 'input') return last ? undefined : { type: 'input', id: Number(first) };
  if (!last) return { type: 'item', id: Number(first) };
  return { type: 'items', from: Number(first), to: Number(last) };
}

export function sourceApiPath(source: SourceRef): string {
  switch (source.type) {
    case 'input':
      return `/api/inputs/${source.id}`;
    case 'item':
      return `/api/items/${source.id}`;
    case 'items':
      return `/api/items?from=${source.from}&to=${source.to}`;
  }
}

/** How the source is cited, e.g. 'input:7' or 'l0:504–519'. */
export function sourceLabel(source: SourceRef): string {
  switch (source.type) {
    case 'input':
      return `input:${source.id}`;
    case 'item':
      return `l0:${source.id}`;
    case 'items':
      return `l0:${source.from}–${source.to}`;
  }
}

const SOURCE_NAMES: Record<string, string> = {
  google_calendar: 'Google Calendar',
  google_contacts: 'Google Contacts',
  google_tasks: 'Google Tasks',
  gmail: 'Gmail',
  outlook_calendar: 'Outlook calendar',
  outlook_mail: 'Outlook mail',
  teams_chats: 'Teams chat',
  planner: 'Planner',
  microsoft_todo: 'Microsoft To Do',
};

/** E.g. 'Outlook mail' for 'outlook_mail'; unknown sources as they are. */
export function sourceName(source: string): string {
  return SOURCE_NAMES[source] ?? source;
}
