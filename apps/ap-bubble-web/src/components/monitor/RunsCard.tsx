import { Card, Table, Text, Title } from '@mantine/core';

import type { JobRun } from '../../api/types';
import { formatDateTime, formatDuration } from '../../lib/dates';
import { jobLabel, scopeLabel } from '../../lib/jobs';
import { ErrorText } from './ErrorText';
import { RunStatusBadge } from './RunStatusBadge';

/** The latest job runs, newest first. */
export function RunsCard({ runs }: { runs: JobRun[] }) {
  return (
    <Card withBorder padding="lg">
      <Title order={3} mb="md">
        Recent runs
      </Title>
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
              <Table.Tr key={run.id}>
                <Table.Td>
                  <Text size="sm">{formatDateTime(run.startedAt)}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{jobLabel(run.jobName)}</Text>
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
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
    </Card>
  );
}
