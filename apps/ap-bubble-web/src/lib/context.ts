import type { Context } from '../api/types';

/** The Overview's quick filter: work, personal, or both. */
export type ContextFilter = 'both' | Context;

export function matchesContext(context: Context, filter: ContextFilter): boolean {
  return filter === 'both' || context === filter;
}
