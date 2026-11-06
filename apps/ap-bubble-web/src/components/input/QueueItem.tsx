import { Group, Paper, Spoiler, Stack, Text } from '@mantine/core';

import type { InputItem } from '../../api/types';
import { formatDateTime } from '../../lib/dates';
import { DeleteInputButton } from './DeleteInputButton';
import { InputFileLink } from './InputFileLink';
import { StatusBadge } from './StatusBadge';

export function QueueItem({ item, onDeleted }: { item: InputItem; onDeleted: () => void }) {
  return (
    <Paper withBorder p="sm">
      <Group justify="space-between" wrap="nowrap" align="flex-start">
        <Stack gap={6} style={{ flex: 1, minWidth: 0 }}>
          <Group gap="xs">
            <StatusBadge status={item.status} />
            <Text size="xs" c="dimmed">
              {formatDateTime(item.createdAt)}
            </Text>
          </Group>
          {item.text && (
            <Spoiler maxHeight={66} showLabel="Show more" hideLabel="Show less">
              <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                {item.text}
              </Text>
            </Spoiler>
          )}
          {item.files.map((file) => (
            <InputFileLink key={file.id} file={file} />
          ))}
          {item.error && (
            <Text size="xs" c="red">
              {item.error}
            </Text>
          )}
        </Stack>
        {item.status === 'queued' && <DeleteInputButton inputId={item.id} onDeleted={onDeleted} />}
      </Group>
    </Paper>
  );
}
