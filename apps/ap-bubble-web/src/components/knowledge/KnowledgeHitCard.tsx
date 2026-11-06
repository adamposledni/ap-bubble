import { Group, Paper, Stack, Text, UnstyledButton } from '@mantine/core';
import { Link, useLocation } from 'react-router';

import type { KnowledgeHit } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { docPath, type KnowledgeNavState } from '../../lib/knowledge';
import { FolderBadge } from './FolderBadge';
import { SnippetText } from './SnippetText';
import { TagList } from './TagList';

export function KnowledgeHitCard({ hit }: { hit: KnowledgeHit }) {
  const state: KnowledgeNavState = { search: useLocation().search };
  const to = docPath(hit.folder, hit.slug);

  return (
    <UnstyledButton component={Link} to={to} state={state} display="block">
      <Paper withBorder p="sm">
        <Stack gap={6}>
          <Group justify="space-between" wrap="nowrap" align="flex-start">
            <Group gap="xs">
              <Text fw={500} c="indigo">
                {hit.name}
              </Text>
              <FolderBadge folder={hit.folder} />
              <TagList tags={hit.tags} />
            </Group>
            {hit.updated && (
              <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
                {formatDate(hit.updated)}
              </Text>
            )}
          </Group>
          <SnippetText parts={hit.snippet} />
        </Stack>
      </Paper>
    </UnstyledButton>
  );
}
