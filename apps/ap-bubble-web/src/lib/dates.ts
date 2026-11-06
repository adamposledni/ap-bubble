// Local-time helpers. Days are YYYY-MM-DD strings in the browser's time zone.

export const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

const dayFormat = new Intl.DateTimeFormat(undefined, {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
});
const shortDayFormat = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' });
const timeFormat = new Intl.DateTimeFormat(undefined, {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
});
const dateTimeFormat = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
  hourCycle: 'h23',
});

export function today(): string {
  return dayOf(new Date());
}

export function dayOf(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function addDays(day: string, days: number): string {
  const date = parseDay(day);
  date.setDate(date.getDate() + days);
  return dayOf(date);
}

export function parseDay(day: string): Date {
  const [year, month, date] = day.split('-').map(Number);
  return new Date(year, month - 1, date);
}

export function formatDay(day: string): string {
  return dayFormat.format(parseDay(day));
}

export function formatShortDay(day: string): string {
  return shortDayFormat.format(parseDay(day));
}

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' });

/** E.g. "6 Nov 2026"; anything but YYYY-MM-DD is returned as is. */
export function formatDate(day: string): string {
  return /^\d{4}-\d{2}-\d{2}$/.test(day) ? dateFormat.format(parseDay(day)) : day;
}

export function formatTime(timestamp: string): string {
  return timeFormat.format(new Date(timestamp));
}

export function formatDateTime(timestamp: string): string {
  return dateTimeFormat.format(new Date(timestamp));
}

const relativeFormat = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
const AGO_STEPS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['second', 60],
  ['minute', 60],
  ['hour', 24],
  ['day', 30],
  ['month', 12],
  ['year', Infinity],
];

/** E.g. "5 minutes ago"; seconds round to "now". */
export function formatAgo(timestamp: string): string {
  let value = (new Date(timestamp).getTime() - Date.now()) / 1000;
  for (const [unit, size] of AGO_STEPS) {
    if (Math.abs(value) < size) {
      const rounded = unit === 'second' ? 0 : Math.round(value);
      return relativeFormat.format(rounded, unit);
    }
    value /= size;
  }
  return formatDateTime(timestamp);
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)} s`;
  return `${Math.floor(seconds / 60)} min ${Math.round(seconds % 60)} s`;
}
