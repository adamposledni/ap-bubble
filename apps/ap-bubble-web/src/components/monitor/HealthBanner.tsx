import { Alert } from '@mantine/core';
import { IconAlertTriangle, IconCircleCheck, IconClockExclamation } from '@tabler/icons-react';

import type { JobStatus } from '../../api/types';
import { jobLabel } from '../../lib/jobs';

/** Red when a job failed on its last run, yellow when data is stale, green otherwise. */
export function HealthBanner({ jobs }: { jobs: JobStatus[] }) {
  const failed = jobs.filter((job) => job.lastStatus === 'failed');
  const stale = jobs.filter((job) => job.stale && job.lastStatus !== 'failed');

  if (jobs.length === 0) {
    return <Alert color="gray">No job has run yet.</Alert>;
  }
  if (failed.length > 0) {
    return (
      <Alert color="red" icon={<IconAlertTriangle size={18} />} title="Sync failed">
        Last run failed: {names(failed)}.
      </Alert>
    );
  }
  if (stale.length > 0) {
    return (
      <Alert color="yellow" icon={<IconClockExclamation size={18} />} title="Data is stale">
        Not synced in the last 24 hours: {names(stale)}. Ingest is not scheduled yet; run
        tools/ingest.ps1 sync &lt;source&gt;.
      </Alert>
    );
  }
  return (
    <Alert color="green" icon={<IconCircleCheck size={18} />}>
      All sources synced in the last 24 hours.
    </Alert>
  );
}

function names(jobs: JobStatus[]): string {
  return [...new Set(jobs.map((job) => jobLabel(job.jobName)))].join(', ');
}
