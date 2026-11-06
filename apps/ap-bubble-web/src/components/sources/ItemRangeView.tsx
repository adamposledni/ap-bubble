import { Stack, Text, Title } from '@mantine/core';

import type { ItemRange } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { sourceApiPath, sourceLabel, type SourceRef } from '../../lib/sources';
import { Loadable } from '../common/Loadable';
import { ItemRow } from './ItemRow';

/** A range of L0 items (l0:A–B), each opening on click. */
export function ItemRangeView({ from, to }: { from: number; to: number }) {
  const source: SourceRef = { type: 'items', from, to };
  const { data, error, loading } = useApi<ItemRange>(sourceApiPath(source));

  return (
    <Loadable loading={loading} error={error} hasData={data !== undefined}>
      {data && (
        <Stack gap="xs">
          <Title order={3}>{sourceLabel(source)}</Title>
          <Text size="sm" c="dimmed">
            {countLabel(data)}
          </Text>
          {data.items.map((item) => (
            <ItemRow key={item.id} item={item} />
          ))}
        </Stack>
      )}
    </Loadable>
  );
}

function countLabel({ items, truncated }: ItemRange): string {
  const count = `${items.length} ${items.length === 1 ? 'item' : 'items'}`;
  return truncated ? `${count}, from the start of the range only` : count;
}
