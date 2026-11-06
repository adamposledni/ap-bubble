import { Alert, Group, Loader, Progress, Stack, Text } from '@mantine/core';

import type { RunningJob } from '../../api/types';
import { formatDuration } from '../../lib/dates';
import { jobLabel, scopeLabel } from '../../lib/jobs';
import { DryRunBadge } from './DryRunBadge';

/** What runs right now: job, elapsed time and, for the curator, the batch it is on. */
export function RunningNow({ running }: { running: RunningJob[] }) {
  if (running.length === 0) return null;
  return (
    <Alert color="indigo" py="xs" icon={<Loader size={16} color="indigo" />}>
      <Stack gap="xs">
        {running.map((job) => (
          <RunningRow key={job.run.id} job={job} />
        ))}
      </Stack>
    </Alert>
  );
}

function RunningRow({ job }: { job: RunningJob }) {
  const { run, batchCurrent, batchTotal } = job;
  const elapsed = (Date.now() - new Date(run.startedAt).getTime()) / 1000;
  return (
    <Stack gap={4}>
      <Group gap="xs">
        <Text size="sm" fw={600}>
          {jobLabel(run.jobName)}
        </Text>
        {run.dryRun && <DryRunBadge />}
        {run.scope && (
          <Text size="sm" c="dimmed">
            {scopeLabel(run.scope)}
          </Text>
        )}
        <Text size="sm" c="dimmed">
          running for {formatDuration(Math.max(elapsed, 0))}
        </Text>
        {batchCurrent !== null && batchTotal !== null && (
          <Text size="sm">
            batch {batchCurrent} of {batchTotal}
          </Text>
        )}
      </Group>
      {batchCurrent !== null && batchTotal !== null && (
        <Progress value={((batchCurrent - 1) / batchTotal) * 100} size="xs" color="indigo" animated />
      )}
    </Stack>
  );
}
