import { Group, Paper, Stack, Text, Title } from '@mantine/core';

import type { KnowledgeRef } from '../../api/types';
import { docPath } from '../../lib/knowledge';
import { DocLink } from './DocLink';
import { FolderBadge } from './FolderBadge';

/** "Mentioned in": the knowledge files linking to this one. */
export function Backlinks({ refs }: { refs: KnowledgeRef[] }) {
  return (
    <Paper withBorder p="md">
      <Stack gap="xs">
        <Title order={4}>Mentioned in</Title>
        {refs.length === 0 && (
          <Text size="sm" c="dimmed">
            No other file links here.
          </Text>
        )}
        {refs.map((ref) => (
          <Group key={`${ref.folder}/${ref.slug}`} gap="xs">
            <DocLink to={docPath(ref.folder, ref.slug)}>{ref.name}</DocLink>
            <FolderBadge folder={ref.folder} />
          </Group>
        ))}
      </Stack>
    </Paper>
  );
}
