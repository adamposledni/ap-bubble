import { Stack, Title } from '@mantine/core';

import { Loadable } from '../components/common/Loadable';
import { KnowledgeResults } from '../components/knowledge/KnowledgeResults';
import { KnowledgeSearchBar } from '../components/knowledge/KnowledgeSearchBar';
import { useKnowledgeSearch } from '../hooks/useKnowledgeSearch';

/** Keyword search over the curated knowledge files (L2). */
export function KnowledgePage() {
  const { input, setInput, folder, setFolder, result } = useKnowledgeSearch();
  const { data, error, loading } = result;

  return (
    <Stack gap="md" maw={900}>
      <Title order={2}>Knowledge</Title>
      <KnowledgeSearchBar input={input} onInput={setInput} folder={folder} onFolder={setFolder} />
      <Loadable loading={loading} error={error} hasData={data !== undefined}>
        {data && <KnowledgeResults result={data} />}
      </Loadable>
    </Stack>
  );
}
