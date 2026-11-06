import { createContext, useContext } from 'react';

import type { DocRef } from '../../lib/knowledge';
import type { SourceRef } from '../../lib/sources';

/** What the knowledge dialog can show besides the search: a knowledge file or a cited source. */
export type KnowledgeTarget = { type: 'doc'; doc: DocRef } | { type: 'source'; source: SourceRef };

/** Opens a knowledge file or a source in the knowledge dialog, on top of what it shows. */
export const KnowledgeNavContext = createContext<(target: KnowledgeTarget) => void>(() => {
  console.warn('Knowledge link used outside the knowledge dialog');
});

export function useOpenDoc(): (doc: DocRef) => void {
  const open = useContext(KnowledgeNavContext);
  return (doc) => open({ type: 'doc', doc });
}

export function useOpenSource(): (source: SourceRef) => void {
  const open = useContext(KnowledgeNavContext);
  return (source) => open({ type: 'source', source });
}
