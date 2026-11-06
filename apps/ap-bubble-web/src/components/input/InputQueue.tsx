import { Badge, Button, Group, SegmentedControl, Stack, Text, Title } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';

import type { InputItem } from '../../api/types';
import type { ApiState } from '../../hooks/useApi';
import { Loadable } from '../common/Loadable';
import { PAGE_LIST_MAX_HEIGHT, ScrollCard } from '../common/ScrollCard';
import { QueueItem } from './QueueItem';

/** 'open' hides the inputs the curator has already processed. */
export type QueueView = 'open' | 'all';

interface Props {
  queue: ApiState<InputItem[]>;
  view: QueueView;
  onViewChange: (view: QueueView) => void;
  onNewInput: () => void;
}

/** The L1 queue, newest first; the curator moves items from queued to done (or failed). */
export function InputQueue({ queue, view, onViewChange, onNewInput }: Props) {
  const items = queue.data ?? [];
  const waiting = items.filter((item) => item.status === 'queued').length;

  return (
    <ScrollCard
      maxHeight={PAGE_LIST_MAX_HEIGHT}
      header={
        <Group gap="sm">
          <Title order={4}>Queue</Title>
          <Badge variant="light">{waiting} waiting</Badge>
        </Group>
      }
      actions={
        <Group gap="xs" wrap="nowrap">
          <SegmentedControl
            size="xs"
            value={view}
            onChange={(value) => onViewChange(value as QueueView)}
            data={[
              { value: 'open', label: 'Open' },
              { value: 'all', label: 'All' },
            ]}
          />
          <Button size="xs" leftSection={<IconPlus size={14} />} onClick={onNewInput}>
            New input
          </Button>
        </Group>
      }
    >
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
    </ScrollCard>
  );
}
