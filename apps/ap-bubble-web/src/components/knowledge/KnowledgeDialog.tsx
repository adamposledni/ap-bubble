import { Button, Modal, Stack, Text } from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';

import type { useKnowledgeSearch } from '../../hooks/useKnowledgeSearch';
import type { DocRef } from '../../lib/knowledge';
import { Loadable } from '../common/Loadable';
import { KnowledgeDocView } from './KnowledgeDocView';
import { KnowledgeNavContext } from './KnowledgeNav';
import { KnowledgeResults } from './KnowledgeResults';
import { KnowledgeSearchBar } from './KnowledgeSearchBar';

interface Props {
  opened: boolean;
  onClose: () => void;
  search: ReturnType<typeof useKnowledgeSearch>;
  doc: DocRef | null;
  onDoc: (doc: DocRef | null) => void;
}

/** Knowledge search with its results; a chosen file replaces them until "Back to results". */
export function KnowledgeDialog({ opened, onClose, search, doc, onDoc }: Props) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size="xl"
      title={doc ? <BackToResults onClick={() => onDoc(null)} /> : <Text fw={600}>Knowledge</Text>}
    >
      <KnowledgeNavContext.Provider value={onDoc}>
        {doc ? <KnowledgeDocView doc={doc} /> : <SearchView search={search} />}
      </KnowledgeNavContext.Provider>
    </Modal>
  );
}

function SearchView({ search }: { search: Props['search'] }) {
  const { input, setInput, folder, setFolder, result } = search;
  return (
    <Stack gap="md">
      <KnowledgeSearchBar input={input} onInput={setInput} folder={folder} onFolder={setFolder} />
      <Loadable loading={result.loading} error={result.error} hasData={result.data !== undefined}>
        {result.data && <KnowledgeResults result={result.data} />}
      </Loadable>
    </Stack>
  );
}

function BackToResults({ onClick }: { onClick: () => void }) {
  return (
    <Button
      variant="subtle"
      size="compact-sm"
      leftSection={<IconArrowLeft size={16} stroke={1.5} />}
      onClick={onClick}
    >
      Back to results
    </Button>
  );
}
