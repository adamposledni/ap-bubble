import { Paper, SimpleGrid, Text } from '@mantine/core';

import type { Monitor } from '../../api/types';

export function StatTiles({ monitor }: { monitor: Monitor }) {
  const failed = monitor.jobs.filter((job) => job.lastStatus === 'failed').length;
  const stale = monitor.jobs.filter((job) => job.stale).length;
  const tiles = [
    { label: 'Sources', value: monitor.jobs.length, color: undefined },
    { label: 'Failed', value: failed, color: failed > 0 ? 'red' : undefined },
    { label: 'Stale (24 h)', value: stale, color: stale > 0 ? 'yellow.8' : undefined },
    { label: 'Inputs waiting', value: monitor.queue.queued ?? 0, color: undefined },
  ];

  return (
    <SimpleGrid cols={{ base: 2, sm: 4 }}>
      {tiles.map(({ label, value, color }) => (
        <Paper key={label} withBorder p="md">
          <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
            {label}
          </Text>
          <Text size="xl" fw={700} c={color}>
            {value}
          </Text>
        </Paper>
      ))}
    </SimpleGrid>
  );
}
