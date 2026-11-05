import type { AgendaEvent } from '../../api/types';
import { addDays, dayOf } from '../../lib/dates';

export interface AgendaDay {
  day: string;
  events: AgendaEvent[];
}

/** Every day of the window; an event sits on its start day, or the first day if it began earlier. */
export function groupByDay(events: AgendaEvent[], firstDay: string, days: number): AgendaDay[] {
  const result: AgendaDay[] = Array.from({ length: days }, (_, i) => ({
    day: addDays(firstDay, i),
    events: [],
  }));
  for (const event of events) {
    const start = event.allDay ? event.start : dayOf(new Date(event.start));
    const day = start < firstDay ? firstDay : start;
    result.find((entry) => entry.day === day)?.events.push(event);
  }
  return result;
}
