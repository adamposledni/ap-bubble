import { Code, Drawer, Group, Stack, Text, Title } from '@mantine/core';

import type { JobRun, RunDetail } from '../../api/types';
import { Loadable } from '../common/Loadable';
import { formatDateTime, formatDuration } from '../../lib/dates';
import { jobLabel, scopeLabel } from '../../lib/jobs';
import { useApi } from '../../hooks/useApi';
import { BatchList } from './BatchList';
import { DryRunBadge } from './DryRunBadge';
import { RunStatusBadge } from './RunStatusBadge';

const LIVE_REFRESH_MS = 5_000;

interface Props {
  /** The run to show; null closes the drawer. */
  runId: number | null;
  onClose: () => void;
}

/** One run in full: times, status, items, the whole error and, for the curator, its batches. */
export function RunDrawer({ runId, onClose }: Props) {
  return (
    <Drawer opened={runId !== null} onClose={onClose} position="right" size="xl" title="Run">
      {runId !== null && <RunBody runId={runId} />}
    </Drawer>
  );
}

function RunBody({ runId }: { runId: number }) {
  const { data, error, loading } = useApi<RunDetail>(`/api/monitor/runs/${runId}`, LIVE_REFRESH_MS);
  return (
    <Loadable loading={loading} error={error} hasData={data !== undefined}>
      {data && (
        <Stack gap="md">
          <RunFacts run={data.run} />
          {data.run.error && <RunError error={data.run.error} />}
          {data.run.jobName === 'curator.run' && (
            <Stack gap="xs">
              <Title order={4}>Batches</Title>
              <BatchList runId={runId} batches={data.batches} />
            </Stack>
          )}
        </Stack>
      )}
    </Loadable>
  );
}

function RunFacts({ run }: { run: JobRun }) {
  const facts: [string, string][] = [
    ['Started', formatDateTime(run.startedAt)],
    ['Finished', run.finishedAt ? formatDateTime(run.finishedAt) : '—'],
    ['Duration', run.durationSeconds === null ? '—' : formatDuration(run.durationSeconds)],
    ['Items', run.itemsProcessed.toLocaleString()],
    ['Account', scopeLabel(run.scope)],
  ];
  return (
    <Stack gap="xs">
      <Group gap="xs">
        <Title order={3}>{jobLabel(run.jobName)}</Title>
        {run.dryRun && <DryRunBadge />}
        <RunStatusBadge status={run.status} />
        <Text size="sm" c="dimmed">
          run {run.id}
        </Text>
      </Group>
      {facts.map(([label, value]) => (
        <Group key={label} gap="md" wrap="nowrap">
          <Text size="sm" c="dimmed" w={80}>
            {label}
          </Text>
          <Text size="sm">{value}</Text>
        </Group>
      ))}
    </Stack>
  );
}

function RunError({ error }: { error: string }) {
  return (
    <Stack gap={4}>
      <Title order={4}>Error</Title>
      <Code block c="red" style={{ whiteSpace: 'pre-wrap' }}>
        {error}
      </Code>
    </Stack>
  );
}
