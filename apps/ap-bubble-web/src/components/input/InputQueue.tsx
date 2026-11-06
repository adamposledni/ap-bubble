import { Badge, Card, Group, SegmentedControl, Stack, Text, Title } from '@mantine/core';

import type { InputItem } from '../../api/types';
import type { ApiState } from '../../hooks/useApi';
import { Loadable } from '../common/Loadable';
import { QueueItem } from './QueueItem';

/** 'open' hides the inputs the curator has already processed. */
export type QueueView = 'open' | 'all';

interface Props {
  queue: ApiState<InputItem[]>;
  view: QueueView;
  onViewChange: (view: QueueView) => void;
}

/** The L1 queue, newest first; the curator moves items from queued to done (or failed). */
export function InputQueue({ queue, view, onViewChange }: Props) {
  const items = queue.data ?? [];
  const waiting = items.filter((item) => item.status === 'queued').length;

  return (
    <Card withBorder padding="lg">
      <Group justify="space-between" mb="md">
        <Group gap="sm">
          <Title order={3}>Queue</Title>
          <Badge variant="light">{waiting} waiting</Badge>
        </Group>
        <SegmentedControl
          size="xs"
          value={view}
          onChange={(value) => onViewChange(value as QueueView)}
          data={[
            { value: 'open', label: 'Open' },
            { value: 'all', label: 'All' },
          ]}
        />
      </Group>
      <Loadable loading={queue.loading} error={queue.error} hasData={queue.data !== undefined}>
        {items.length === 0 ? (
          <Text size="sm" c="dimmed">
            {view === 'open' ? 'Nothing open.' : 'Nothing yet.'}
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
