import { Group, Stack } from '@mantine/core';
import { useState } from 'react';

import type { Monitor } from '../api/types';
import { Loadable } from '../components/common/Loadable';
import { HealthBanner } from '../components/monitor/HealthBanner';
import { JobsCard } from '../components/monitor/JobsCard';
import { RefreshControl } from '../components/monitor/RefreshControl';
import { RunDrawer } from '../components/monitor/RunDrawer';
import { RunningNow } from '../components/monitor/RunningNow';
import { RunsCard } from '../components/monitor/RunsCard';
import { StatTiles } from '../components/monitor/StatTiles';
import { useApi } from '../hooks/useApi';
import { jobKey, jobLabel, scopeLabel } from '../lib/jobs';

const REFRESH_MS = 30_000;
const REFRESH_WHILE_RUNNING_MS = 5_000;

/** Health of the jobs (ingest, curator) and their runs, from the LM job log. */
export function MonitorPage() {
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);
  const [runningNow, setRunningNow] = useState(false);
  const { data, updatedAt, error, loading, reload } = useApi<Monitor>(
    '/api/monitor',
    runningNow ? REFRESH_WHILE_RUNNING_MS : REFRESH_MS,
  );
  if (data && (data.running.length > 0) !== runningNow) setRunningNow(data.running.length > 0);

  const job = data?.jobs.find((j) => jobKey(j.jobName, j.scope) === selectedJob);
  const runs = (data?.runs ?? []).filter(
    (run) => !job || (run.jobName === job.jobName && run.scope === job.scope),
  );

  return (
    <Stack gap="md">
      <Group justify="flex-end">
        <RefreshControl loading={loading} updatedAt={updatedAt} onRefresh={reload} />
      </Group>
      <Loadable loading={loading} error={error} hasData={data !== undefined}>
        {data && (
          <Stack gap="md">
            <RunningNow running={data.running} />
            <HealthBanner jobs={data.jobs} />
            <StatTiles monitor={data} />
            <JobsCard jobs={data.jobs} selected={selectedJob} onSelect={setSelectedJob} />
            <RunsCard
              runs={runs}
              filterLabel={job ? jobFilterLabel(job.jobName, job.scope) : null}
              onClearFilter={() => setSelectedJob(null)}
              selectedRunId={selectedRun}
              onSelectRun={setSelectedRun}
            />
          </Stack>
        )}
      </Loadable>
      <RunDrawer runId={selectedRun} onClose={() => setSelectedRun(null)} />
    </Stack>
  );
}

function jobFilterLabel(jobName: string, scope: string | null): string {
  return scope ? `${jobLabel(jobName)} · ${scopeLabel(scope)}` : jobLabel(jobName);
}
