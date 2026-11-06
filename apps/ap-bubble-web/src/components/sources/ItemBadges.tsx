import { Badge, Group } from '@mantine/core';

import type { ItemSummary } from '../../api/types';
import { sourceName } from '../../lib/sources';

/** Kind, source and context of an L0 item, and whether the source deleted it. */
export function ItemBadges({ item }: { item: ItemSummary }) {
  return (
    <Group gap={6} wrap="nowrap">
      <Badge size="sm" variant="light">
        {item.kind}
      </Badge>
      <Badge size="sm" variant="light" color="gray" tt="none">
        {sourceName(item.source)}
      </Badge>
      <Badge size="sm" variant="outline" color="gray">
        {item.account.context}
      </Badge>
      {item.deleted && (
        <Badge size="sm" variant="light" color="red">
          deleted
        </Badge>
      )}
    </Group>
  );
}
