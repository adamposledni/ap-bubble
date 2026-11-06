import { Badge, Button, Code, Collapse, Group, Loader, Paper, Stack, Text } from '@mantine/core';
import { useState } from 'react';

import type { Batch, BatchStatus } from '../../api/types';
import { formatDuration } from '../../lib/dates';
import { useText } from '../../hooks/useText';

const COLORS: Record<BatchStatus, string> = {
  done: 'green',
  failed: 'red',
  running: 'indigo',
  pending: 'gray',
  not_sent: 'gray',
};

const LABELS: Record<BatchStatus, string> = {
  done: 'done',
  failed: 'failed',
  running: 'running',
  pending: 'pending',
  not_sent: 'not sent',
};

/** The batches of a curator run: Claude's result per batch and the batch file on demand. */
export function BatchList({ runId, batches }: { runId: number; batches: Batch[] }) {
  if (batches.length === 0) {
    return (
      <Text size="sm" c="dimmed">
        This run wrote no batch files.
      </Text>
    );
  }
  return (
    <Stack gap="xs">
      {batches.map((batch) => (
        <BatchRow key={batch.name} runId={runId} batch={batch} />
      ))}
    </Stack>
  );
}

function BatchRow({ runId, batch }: { runId: number; batch: Batch }) {
  const [open, setOpen] = useState(false);
  return (
    <Paper withBorder p="sm">
      <Group justify="space-between">
        <Group gap="xs">
          <Text size="sm" fw={500}>
            {batch.name}
          </Text>
          <Badge size="sm" variant="light" color={COLORS[batch.status]}>
            {LABELS[batch.status]}
          </Badge>
        </Group>
        <Button size="compact-xs" variant="subtle" onClick={() => setOpen((value) => !value)}>
          {open ? 'Hide batch file' : 'View batch file'}
        </Button>
      </Group>
      <BatchFacts batch={batch} />
      {batch.summary && (
        <Text size="sm" mt="xs" style={{ whiteSpace: 'pre-wrap' }}>
          {batch.summary}
        </Text>
      )}
      <Collapse in={open} mt="xs">
        {open && <BatchFile runId={runId} name={batch.name} />}
      </Collapse>
    </Paper>
  );
}

function BatchFacts({ batch }: { batch: Batch }) {
  const facts = [
    batch.numTurns !== null && `${batch.numTurns} turns`,
    batch.durationSeconds !== null && formatDuration(batch.durationSeconds),
    batch.costUsd !== null && `$${batch.costUsd.toFixed(2)}`,
  ].filter(Boolean);
  if (facts.length === 0) return null;
  return (
    <Text size="xs" c="dimmed" mt={4}>
      {facts.join(' · ')}
    </Text>
  );
}

function BatchFile({ runId, name }: { runId: number; name: string }) {
  const { text, error } = useText(`/api/monitor/runs/${runId}/batches/${name}`);
  if (error) return <Text size="sm" c="red">{error}</Text>;
  if (text === undefined) return <Loader size="xs" />;
  return (
    <Code block mah={400} style={{ overflow: 'auto' }}>
      {text}
    </Code>
  );
}
