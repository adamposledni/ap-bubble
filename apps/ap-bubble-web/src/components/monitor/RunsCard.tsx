import { Badge, Button, Card, Group, Table, Text, Title } from '@mantine/core';

import type { JobRun } from '../../api/types';
import { formatDateTime, formatDuration } from '../../lib/dates';
import { jobLabel, scopeLabel } from '../../lib/jobs';
import { DryRunBadge } from './DryRunBadge';
import { ErrorText } from './ErrorText';
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
  return (
    <Card withBorder padding="lg">
      <Group justify="space-between" mb="md">
        <Group gap="xs">
          <Title order={3}>Recent runs</Title>
          <Text size="sm" c="dimmed">
            last 7 days
          </Text>
          {filterLabel && (
            <Badge variant="light" color="indigo">
              {filterLabel}
            </Badge>
          )}
        </Group>
        {filterLabel && (
          <Button size="xs" variant="subtle" onClick={onClearFilter}>
            Show all
          </Button>
        )}
      </Group>
      <Table.ScrollContainer minWidth={720}>
        <Table verticalSpacing={6} striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Started</Table.Th>
              <Table.Th>Job</Table.Th>
              <Table.Th>Account</Table.Th>
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
                active={run.id === selectedRunId}
                onClick={() => onSelectRun(run.id)}
              />
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
      {runs.length === 0 && (
        <Text size="sm" c="dimmed" mt="sm">
          No runs in the last 7 days.
        </Text>
      )}
    </Card>
  );
}

function RunRow({ run, active, onClick }: { run: JobRun; active: boolean; onClick: () => void }) {
  return (
    <Table.Tr
      onClick={onClick}
      style={{ cursor: 'pointer' }}
      bg={active ? 'var(--mantine-color-indigo-light)' : undefined}
    >
      <Table.Td>
        <Text size="sm">{formatDateTime(run.startedAt)}</Text>
      </Table.Td>
      <Table.Td>
        <Group gap="xs">
          <Text size="sm">{jobLabel(run.jobName)}</Text>
          {run.dryRun && <DryRunBadge />}
        </Group>
      </Table.Td>
      <Table.Td>
        <Text size="sm" c="dimmed">
          {scopeLabel(run.scope)}
        </Text>
      </Table.Td>
      <Table.Td>
        <RunStatusBadge status={run.status} />
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
