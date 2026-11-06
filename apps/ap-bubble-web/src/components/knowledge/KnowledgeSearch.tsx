import { Kbd, TextInput } from '@mantine/core';
import { useDisclosure, useHotkeys } from '@mantine/hooks';
import { IconSearch } from '@tabler/icons-react';

import { useKnowledgeSearch } from '../../hooks/useKnowledgeSearch';
import { useNavStack } from '../../hooks/useNavStack';
import { KnowledgeDialog } from './KnowledgeDialog';
import type { KnowledgeTarget } from './KnowledgeNav';

/** Search bar that opens the knowledge dialog (also Ctrl+K); closing it clears the search text. */
export function KnowledgeSearch() {
  const [opened, { open, close }] = useDisclosure(false);
  const nav = useNavStack<KnowledgeTarget>();
  const search = useKnowledgeSearch();
  useHotkeys([['mod+K', open]]);

  const onClose = () => {
    close();
    nav.reset();
    search.setInput('');
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
      <KnowledgeDialog opened={opened} onClose={onClose} search={search} nav={nav} />
    </>
  );
}
