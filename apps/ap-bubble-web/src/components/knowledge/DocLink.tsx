import { Anchor } from '@mantine/core';
import type { ReactNode } from 'react';

import type { DocRef } from '../../lib/knowledge';
import { useOpenDoc } from './KnowledgeNav';

/** Link from one knowledge file to another, opened in the same dialog. */
export function DocLink({ doc, children }: { doc: DocRef; children: ReactNode }) {
  const openDoc = useOpenDoc();
  return (
    <Anchor component="button" type="button" fz="inherit" onClick={() => openDoc(doc)}>
      {children}
    </Anchor>
  );
}
