import { Group, Text } from '@mantine/core';

import type { Monitor } from '../../api/types';

/** Key counts as one compact line of label/value pairs. */
export function StatTiles({ monitor }: { monitor: Monitor }) {
  const failed = monitor.jobs.filter((job) => job.lastStatus === 'failed').length;
  const stale = monitor.jobs.filter((job) => job.stale).length;
  const stats = [
    { label: 'Jobs', value: monitor.jobs.length, color: undefined },
    { label: 'Failed', value: failed, color: failed > 0 ? 'red' : undefined },
    { label: 'Stale', value: stale, color: stale > 0 ? 'yellow.8' : undefined },
  ];

  return (
    <Group gap="md">
      {stats.map(({ label, value, color }) => (
        <Group key={label} gap={4} wrap="nowrap">
          <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
            {label}
          </Text>
          <Text size="sm" fw={700} c={color}>
            {value}
          </Text>
        </Group>
      ))}
    </Group>
  );
}
