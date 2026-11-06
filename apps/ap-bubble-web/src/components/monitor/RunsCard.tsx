import { Badge, Button, Group, Table, Text, Title } from '@mantine/core';

import type { JobRun } from '../../api/types';
import { formatDateTime, formatDuration } from '../../lib/dates';
import { jobLabel, scopeLabel } from '../../lib/jobs';
import { DryRunBadge } from './DryRunBadge';
import { ErrorText } from './ErrorText';
import { MonitorCard } from './MonitorCard';
import { RunStatusBadge } from './RunStatusBadge';

interface Props {
  runs: JobRun[];
  /** Label of the job the list is filtered to, if any. */
  filterLabel: string | null;
  onClearFilter: () => void;
  selectedRunId: number | null;
  onSelectRun: (id: number) => void;
}

/** The job runs of the last 7 days, newest first; click a run for its detail. */
export function RunsCard({ runs, filterLabel, onClearFilter, selectedRunId, onSelectRun }: Props) {
  const showJob = filterLabel === null;
  return (
    <MonitorCard
      header={<RunsHeader filterLabel={filterLabel} />}
      actions={
        filterLabel && (
          <Button size="compact-xs" variant="subtle" onClick={onClearFilter}>
            Show all
          </Button>
        )
      }
    >
      <Table stickyHeader verticalSpacing={6} striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Started</Table.Th>
            {showJob && <Table.Th>Job</Table.Th>}
            <Table.Th>Status</Table.Th>
            <Table.Th ta="right">Duration</Table.Th>
            <Table.Th ta="right">Items</Table.Th>
            <Table.Th>Error</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {runs.map((run) => (
            <RunRow
              key={run.id}
              run={run}
              showJob={showJob}
              active={run.id === selectedRunId}
              onClick={() => onSelectRun(run.id)}
            />
          ))}
        </Table.Tbody>
      </Table>
      {runs.length === 0 && (
        <Text size="sm" c="dimmed" mt="sm">
          No runs in the last 7 days.
        </Text>
      )}
    </MonitorCard>
  );
}

function RunsHeader({ filterLabel }: { filterLabel: string | null }) {
  return (
    <Group gap="xs" wrap="nowrap">
      <Title order={4}>Recent runs</Title>
      <Text size="xs" c="dimmed">
        7 days
      </Text>
      {filterLabel && (
        <Badge variant="light" color="indigo" tt="none">
          {filterLabel}
        </Badge>
      )}
    </Group>
  );
}

interface RunRowProps {
  run: JobRun;
  showJob: boolean;
  active: boolean;
  onClick: () => void;
}

function RunRow({ run, showJob, active, onClick }: RunRowProps) {
  return (
    <Table.Tr
      onClick={onClick}
      style={{ cursor: 'pointer' }}
      bg={active ? 'var(--mantine-color-indigo-light)' : undefined}
    >
      <Table.Td>
        <Text size="sm" style={{ whiteSpace: 'nowrap' }}>
          {formatDateTime(run.startedAt)}
        </Text>
      </Table.Td>
      {showJob && (
        <Table.Td>
          <RunJob run={run} />
        </Table.Td>
      )}
      <Table.Td>
        <Group gap={4} wrap="nowrap">
          <RunStatusBadge status={run.status} />
          {!showJob && run.dryRun && <DryRunBadge />}
        </Group>
      </Table.Td>
      <Table.Td ta="right">
        <Text size="sm">
          {run.durationSeconds === null ? '—' : formatDuration(run.durationSeconds)}
        </Text>
      </Table.Td>
      <Table.Td ta="right">
        <Text size="sm">{run.itemsProcessed.toLocaleString()}</Text>
      </Table.Td>
      <Table.Td>
        <ErrorText error={run.error} />
      </Table.Td>
    </Table.Tr>
  );
}

function RunJob({ run }: { run: JobRun }) {
  return (
    <Group gap={6} style={{ rowGap: 0 }}>
      <Text size="sm">{jobLabel(run.jobName)}</Text>
      {run.scope && (
        <Text size="xs" c="dimmed">
          {scopeLabel(run.scope)}
        </Text>
      )}
      {run.dryRun && <DryRunBadge />}
    </Group>
  );
}
