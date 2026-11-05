import { Badge, Card, Group, Stack, Text, Title } from '@mantine/core';

import type { InputItem } from '../../api/types';
import type { ApiState } from '../../hooks/useApi';
import { Loadable } from '../common/Loadable';
import { QueueItem } from './QueueItem';

/** The L1 queue, newest first; the curator moves items from queued to done (or failed). */
export function InputQueue({ queue }: { queue: ApiState<InputItem[]> }) {
  const items = queue.data ?? [];
  const waiting = items.filter((item) => item.status === 'queued').length;

  return (
    <Card withBorder padding="lg">
      <Group justify="space-between" mb="md">
        <Title order={3}>Queue</Title>
        <Badge variant="light">{waiting} waiting</Badge>
      </Group>
      <Loadable loading={queue.loading} error={queue.error} hasData={queue.data !== undefined}>
        {items.length === 0 ? (
          <Text size="sm" c="dimmed">
            Nothing yet.
          </Text>
        ) : (
          <Stack gap="xs">
            {items.map((item) => (
              <QueueItem key={item.id} item={item} onDeleted={queue.reload} />
            ))}
          </Stack>
        )}
      </Loadable>
    </Card>
  );
}
