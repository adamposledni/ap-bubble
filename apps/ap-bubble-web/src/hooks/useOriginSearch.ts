import { useLocation } from 'react-router';

import type { KnowledgeNavState } from '../lib/knowledge';

/** On a knowledge file page: the search (?q=...) it was reached from, '' if none. */
export function useOriginSearch(): string {
  const state = useLocation().state as KnowledgeNavState | null;
  return state?.search ?? '';
}
