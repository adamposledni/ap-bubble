import { Stack } from '@mantine/core';

import type { Monitor } from '../api/types';
import { Loadable } from '../components/common/Loadable';
import { HealthBanner } from '../components/monitor/HealthBanner';
import { RunsCard } from '../components/monitor/RunsCard';
import { SourcesCard } from '../components/monitor/SourcesCard';
import { StatTiles } from '../components/monitor/StatTiles';
import { useApi } from '../hooks/useApi';

const REFRESH_MS = 30_000;

/** Health of ingest (and later curator) jobs, from the LM job log. */
export function MonitorPage() {
  const { data, error, loading } = useApi<Monitor>('/api/monitor', REFRESH_MS);

  return (
    <Loadable loading={loading} error={error} hasData={data !== undefined}>
      {data && (
        <Stack gap="md">
          <HealthBanner jobs={data.jobs} />
          <StatTiles monitor={data} />
          <SourcesCard jobs={data.jobs} />
          <RunsCard runs={data.runs} />
        </Stack>
      )}
    </Loadable>
  );
}
