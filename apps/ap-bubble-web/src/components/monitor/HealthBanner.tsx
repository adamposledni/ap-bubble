import { Group, Text, Tooltip } from '@mantine/core';
import { IconAlertTriangle, IconCircleCheck, IconClockExclamation } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import type { JobStatus } from '../../api/types';
import { jobLabel } from '../../lib/jobs';

const STALE_HINT = 'Ingest is not scheduled yet; run tools/ingest.ps1 sync <source>.';

/** One line: red when a job failed on its last run, yellow when data is stale, green otherwise. */
export function HealthBanner({ jobs }: { jobs: JobStatus[] }) {
  const failed = jobs.filter((job) => job.lastStatus === 'failed');
  const stale = jobs.filter((job) => job.stale && job.lastStatus !== 'failed');

  if (jobs.length === 0) {
    return <HealthLine color="dimmed" icon={null} text="No job has run yet." />;
  }
  if (failed.length > 0) {
    return (
      <HealthLine
        color="red"
        icon={<IconAlertTriangle size={16} />}
        text={`Last run failed: ${names(failed)}`}
      />
    );
  }
  if (stale.length > 0) {
    return (
      <Tooltip label={STALE_HINT} withArrow>
        <div>
          <HealthLine
            color="yellow.8"
            icon={<IconClockExclamation size={16} />}
            text={`Stale (no sync in 24 h): ${names(stale)}`}
          />
        </div>
      </Tooltip>
    );
  }
  return (
    <HealthLine color="green" icon={<IconCircleCheck size={16} />} text="All jobs healthy (24 h)" />
  );
}

function HealthLine({ color, icon, text }: { color: string; icon: ReactNode; text: string }) {
  return (
    <Group gap={6} wrap="nowrap" c={color}>
      {icon}
      <Text size="sm" fw={500} c={color}>
        {text}
      </Text>
    </Group>
  );
}

function names(jobs: JobStatus[]): string {
  return [...new Set(jobs.map((job) => jobLabel(job.jobName)))].join(', ');
}
