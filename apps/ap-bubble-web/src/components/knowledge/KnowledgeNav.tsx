import { createContext, useContext } from 'react';

import type { DocRef } from '../../lib/knowledge';

/** Opens a knowledge file in the knowledge dialog. */
export const KnowledgeNavContext = createContext<(doc: DocRef) => void>(() => {
  console.warn('Knowledge link used outside the knowledge dialog');
});

export function useOpenDoc(): (doc: DocRef) => void {
  return useContext(KnowledgeNavContext);
}
