import { Group, Text } from '@mantine/core';
import { IconChecks, IconHourglass } from '@tabler/icons-react';

import type { Monitor } from '../../api/types';

/** Whether anything waits for the curator: queued inputs and L0 changes past its cursor. */
export function CurationStatus({ monitor }: { monitor: Monitor }) {
  const inputs = (monitor.queue.queued ?? 0) + (monitor.queue.processing ?? 0);
  const changes = monitor.changesWaiting;
  const waiting = inputs + changes > 0;

  return (
    <Group gap={6} wrap="nowrap" c={waiting ? 'indigo' : 'dimmed'}>
      {waiting ? <IconHourglass size={16} /> : <IconChecks size={16} />}
      <Text size="sm" fw={500} c={waiting ? 'indigo' : 'dimmed'}>
        {waiting
          ? `To curate: ${count(inputs, 'input')}, ${count(changes, 'change')}`
          : 'Everything curated'}
      </Text>
    </Group>
  );
}

function count(n: number, noun: string): string {
  return `${n} ${noun}${n === 1 ? '' : 's'}`;
}
