import { Group, Paper } from '@mantine/core';

import type { Monitor } from '../../api/types';
import { CurationStatus } from './CurationStatus';
import { HealthBanner } from './HealthBanner';
import { RefreshControl } from './RefreshControl';
import { StatTiles } from './StatTiles';

interface Props {
  monitor: Monitor | undefined;
  loading: boolean;
  updatedAt: string | undefined;
  onRefresh: () => void;
}

/** One bar with overall health, what waits to be curated, key counts and the refresh control. */
export function MonitorSummary({ monitor, loading, updatedAt, onRefresh }: Props) {
  return (
    <Paper withBorder px="md" py="xs">
      <Group justify="space-between" gap="md">
        <Group gap="xl">
          {monitor && <HealthBanner jobs={monitor.jobs} />}
          {monitor && <CurationStatus monitor={monitor} />}
          {monitor && <StatTiles monitor={monitor} />}
        </Group>
        <RefreshControl loading={loading} updatedAt={updatedAt} onRefresh={onRefresh} />
      </Group>
    </Paper>
  );
}
