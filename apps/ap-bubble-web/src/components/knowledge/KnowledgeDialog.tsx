import { Button, Modal, Stack, Text } from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';

import type { useKnowledgeSearch } from '../../hooks/useKnowledgeSearch';
import type { NavStack } from '../../hooks/useNavStack';
import { Loadable } from '../common/Loadable';
import { SourceView } from '../sources/SourceView';
import { KnowledgeDocView } from './KnowledgeDocView';
import { KnowledgeNavContext, type KnowledgeTarget } from './KnowledgeNav';
import { KnowledgeResults } from './KnowledgeResults';
import { KnowledgeSearchBar } from './KnowledgeSearchBar';

interface Props {
  opened: boolean;
  onClose: () => void;
  search: ReturnType<typeof useKnowledgeSearch>;
  nav: NavStack<KnowledgeTarget>;
}

/** Knowledge search with its results; an opened file or source replaces them until "Back". */
export function KnowledgeDialog({ opened, onClose, search, nav }: Props) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size="xl"
      title={
        nav.current ? <BackButton depth={nav.depth} onClick={nav.back} /> : <Text fw={600}>Knowledge</Text>
      }
    >
      <KnowledgeNavContext.Provider value={nav.open}>
        {nav.current ? (
          <TargetView key={nav.depth} target={nav.current} />
        ) : (
          <SearchView search={search} />
        )}
      </KnowledgeNavContext.Provider>
    </Modal>
  );
}

function TargetView({ target }: { target: KnowledgeTarget }) {
  return target.type === 'doc' ? <KnowledgeDocView doc={target.doc} /> : <SourceView source={target.source} />;
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

function BackButton({ depth, onClick }: { depth: number; onClick: () => void }) {
  return (
    <Button
      variant="subtle"
      size="compact-sm"
      leftSection={<IconArrowLeft size={16} stroke={1.5} />}
      onClick={onClick}
    >
      {depth > 1 ? 'Back' : 'Back to results'}
    </Button>
  );
}
