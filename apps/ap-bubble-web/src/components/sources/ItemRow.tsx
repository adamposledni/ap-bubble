import { Group, Paper, Text, UnstyledButton } from '@mantine/core';

import type { ItemSummary } from '../../api/types';
import { formatDateOrTime } from '../../lib/dates';
import { useOpenSource } from '../knowledge/KnowledgeNav';
import { ItemBadges } from './ItemBadges';

/** An L0 item of a range, compact; opens the item. */
export function ItemRow({ item }: { item: ItemSummary }) {
  const openSource = useOpenSource();

  return (
    <UnstyledButton display="block" w="100%" onClick={() => openSource({ type: 'item', id: item.id })}>
      <Paper withBorder p="xs">
        <Group justify="space-between" wrap="nowrap" gap="sm">
          <Group gap="sm" wrap="nowrap" style={{ minWidth: 0 }}>
            <Text size="sm" c="indigo" truncate>
              {item.title || '(no title)'}
            </Text>
            <ItemBadges item={item} />
          </Group>
          <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
            {item.startsAt ? formatDateOrTime(item.startsAt) : `l0:${item.id}`}
          </Text>
        </Group>
      </Paper>
    </UnstyledButton>
  );
}
