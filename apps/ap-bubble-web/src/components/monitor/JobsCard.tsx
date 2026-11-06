import { Badge, Group, Stack, Table, Text, TextInput, Title } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';

import type { JobStatus } from '../../api/types';
import { formatAgo, formatDateTime } from '../../lib/dates';
import { jobKey, jobLabel, jobMatches, scopeLabel } from '../../lib/jobs';
import { ErrorText } from './ErrorText';
import { MonitorCard } from './MonitorCard';
import { RunStatusBadge } from './RunStatusBadge';

interface Props {
  jobs: JobStatus[];
  /** jobKey of the selected row, if any. */
  selected: string | null;
  onSelect: (key: string | null) => void;
}

/** One row per job and account: how its last run went and how fresh its data is. */
export function JobsCard({ jobs, selected, onSelect }: Props) {
  const [search, setSearch] = useState('');
  const shown = jobs.filter((job) => jobMatches(job.jobName, job.scope, search));

  return (
    <MonitorCard
      header={<Title order={4}>Jobs</Title>}
      actions={
        <TextInput
          placeholder="Search jobs"
          size="xs"
          leftSection={<IconSearch size={14} />}
          value={search}
          onChange={(event) => setSearch(event.currentTarget.value)}
        />
      }
    >
      <Table stickyHeader verticalSpacing={6} highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Job</Table.Th>
            <Table.Th>Last run</Table.Th>
            <Table.Th>Last success</Table.Th>
            <Table.Th ta="right">Items</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {shown.map((job) => {
            const key = jobKey(job.jobName, job.scope);
            return (
              <JobRow
                key={key}
                job={job}
                active={key === selected}
                onClick={() => onSelect(key === selected ? null : key)}
              />
            );
          })}
        </Table.Tbody>
      </Table>
      {shown.length === 0 && (
        <Text size="sm" c="dimmed" mt="sm">
          No job matches.
        </Text>
      )}
    </MonitorCard>
  );
}

function JobRow({
  job,
  active,
  onClick,
}: {
  job: JobStatus;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <Table.Tr
      onClick={onClick}
      style={{ cursor: 'pointer' }}
      bg={active ? 'var(--mantine-color-indigo-light)' : undefined}
    >
      <Table.Td>
        <JobName job={job} />
      </Table.Td>
      <Table.Td>
        <Stack gap={2}>
          <Group gap="xs" wrap="nowrap">
            <RunStatusBadge status={job.lastStatus} />
            <Text size="xs" c="dimmed" title={formatDateTime(job.lastStartedAt)}>
              {formatAgo(job.lastStartedAt)}
            </Text>
          </Group>
          <ErrorText error={job.lastError} />
        </Stack>
      </Table.Td>
      <Table.Td>
        <LastSuccess job={job} />
      </Table.Td>
      <Table.Td ta="right">
        <Text size="sm">{job.itemsInL0?.toLocaleString() ?? '—'}</Text>
      </Table.Td>
    </Table.Tr>
  );
}

function JobName({ job }: { job: JobStatus }) {
  return (
    <Group gap={6} style={{ rowGap: 0 }}>
      <Text size="sm" fw={500}>
        {jobLabel(job.jobName)}
      </Text>
      {job.scope && (
        <Text size="xs" c="dimmed">
          {scopeLabel(job.scope)}
        </Text>
      )}
    </Group>
  );
}

function LastSuccess({ job }: { job: JobStatus }) {
  if (!job.lastSuccessAt) {
    return (
      <Text size="sm" c="dimmed">
        never
      </Text>
    );
  }
  return (
    <Group gap="xs" wrap="nowrap">
      <Text size="sm" title={formatDateTime(job.lastSuccessAt)}>
        {formatAgo(job.lastSuccessAt)}
      </Text>
      {job.stale && (
        <Badge size="xs" variant="light" color="yellow">
          stale
        </Badge>
      )}
    </Group>
  );
}
