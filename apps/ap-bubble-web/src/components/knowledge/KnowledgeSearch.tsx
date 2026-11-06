import { Kbd, TextInput } from '@mantine/core';
import { useDisclosure, useHotkeys } from '@mantine/hooks';
import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';

import { useKnowledgeSearch } from '../../hooks/useKnowledgeSearch';
import type { DocRef } from '../../lib/knowledge';
import { KnowledgeDialog } from './KnowledgeDialog';

/** Search bar that opens the knowledge dialog (also Ctrl+K); the search survives closing it. */
export function KnowledgeSearch() {
  const [opened, { open, close }] = useDisclosure(false);
  const [doc, setDoc] = useState<DocRef | null>(null);
  const search = useKnowledgeSearch();
  useHotkeys([['mod+K', open]]);

  const onClose = () => {
    close();
    setDoc(null);
  };

  return (
    <>
      <TextInput
        style={{ flex: 1, minWidth: 220 }}
        styles={{ input: { cursor: 'pointer' } }}
        placeholder="Search knowledge"
        leftSection={<IconSearch size={16} stroke={1.5} />}
        rightSection={<Kbd size="xs">Ctrl K</Kbd>}
        rightSectionWidth={56}
        value={search.input}
        readOnly
        onClick={open}
        onKeyDown={(event) => event.key === 'Enter' && open()}
        aria-label="Search knowledge"
      />
      <KnowledgeDialog opened={opened} onClose={onClose} search={search} doc={doc} onDoc={setDoc} />
    </>
  );
}
