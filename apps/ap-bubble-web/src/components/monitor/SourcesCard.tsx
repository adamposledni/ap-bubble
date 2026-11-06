import { Badge, Card, Group, Stack, Table, Text, Title } from '@mantine/core';

import type { JobStatus } from '../../api/types';
import { formatAgo, formatDateTime } from '../../lib/dates';
import { jobLabel, scopeLabel } from '../../lib/jobs';
import { ErrorText } from './ErrorText';
import { RunStatusBadge } from './RunStatusBadge';

/** One row per job and account: how its last run went and how fresh its data is. */
export function SourcesCard({ jobs }: { jobs: JobStatus[] }) {
  return (
    <Card withBorder padding="lg">
      <Title order={3} mb="md">
        Sources
      </Title>
      <Table.ScrollContainer minWidth={640}>
        <Table verticalSpacing="xs" highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Source</Table.Th>
              <Table.Th>Account</Table.Th>
              <Table.Th>Last run</Table.Th>
              <Table.Th>Last success</Table.Th>
              <Table.Th ta="right">Items</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {jobs.map((job) => (
              <SourceRow key={`${job.jobName}|${job.scope}`} job={job} />
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
    </Card>
  );
}

function SourceRow({ job }: { job: JobStatus }) {
  return (
    <Table.Tr>
      <Table.Td>
        <Text size="sm" fw={500}>
          {jobLabel(job.jobName)}
        </Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm" c="dimmed">
          {scopeLabel(job.scope)}
        </Text>
      </Table.Td>
      <Table.Td>
        <Stack gap={2}>
          <Group gap="xs">
            <RunStatusBadge status={job.lastStatus} />
            <Text size="xs" c="dimmed" title={formatDateTime(job.lastStartedAt)}>
              {formatAgo(job.lastStartedAt)}
            </Text>
          </Group>
          <ErrorText error={job.lastError} />
        </Stack>
      </Table.Td>
      <Table.Td>
        {job.lastSuccessAt ? (
          <Group gap="xs">
            <Text size="sm" title={formatDateTime(job.lastSuccessAt)}>
              {formatAgo(job.lastSuccessAt)}
            </Text>
            {job.stale && (
              <Badge size="xs" variant="light" color="yellow">
                stale
              </Badge>
            )}
          </Group>
        ) : (
          <Text size="sm" c="dimmed">
            never
          </Text>
        )}
      </Table.Td>
      <Table.Td ta="right">
        <Text size="sm">{job.itemsInL0?.toLocaleString() ?? '—'}</Text>
      </Table.Td>
    </Table.Tr>
  );
}
