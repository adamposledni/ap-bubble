import { Anchor } from '@mantine/core';

import { parseSourceRef } from '../../lib/sources';
import { useOpenSource } from './KnowledgeNav';

/** One source reference inside a citation (input:7, l0:123, l0:504–519), opened in the dialog. */
export function CitationLink({ text }: { text: string }) {
  const openSource = useOpenSource();
  const source = parseSourceRef(text);
  if (!source) return <>{text}</>;
  return (
    <Anchor component="button" type="button" fz="inherit" ff="inherit" onClick={() => openSource(source)}>
      {text}
    </Anchor>
  );
}
