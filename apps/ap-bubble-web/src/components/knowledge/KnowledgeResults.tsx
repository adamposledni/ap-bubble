import { Stack, Text } from '@mantine/core';

import type { KnowledgeSearch } from '../../api/types';
import { KnowledgeHitCard } from './KnowledgeHitCard';

export function KnowledgeResults({ result }: { result: KnowledgeSearch }) {
  const { total, hits } = result;
  if (total === 0) {
    return (
      <Text size="sm" c="dimmed">
        Nothing found.
      </Text>
    );
  }
  return (
    <Stack gap="xs">
      <Text size="sm" c="dimmed">
        {hits.length < total ? `Showing ${hits.length} of ${total} files` : `${total} files`}
      </Text>
      {hits.map((hit) => (
        <KnowledgeHitCard key={`${hit.folder}/${hit.slug}`} hit={hit} />
      ))}
    </Stack>
  );
}
