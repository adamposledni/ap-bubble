import { Anchor, Group, Paper, Spoiler, Stack, Text } from '@mantine/core';
import { IconPaperclip } from '@tabler/icons-react';

import type { InputItem } from '../../api/types';
import { formatDateTime } from '../../lib/dates';
import { formatSize } from '../../lib/format';
import { DeleteInputButton } from './DeleteInputButton';
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
            <Group key={file.id} gap={6} wrap="nowrap">
              <IconPaperclip size={14} stroke={1.5} />
              <Anchor href={`/api/inputs/files/${file.id}`} size="sm" truncate>
                {file.name}
              </Anchor>
              <Text size="xs" c="dimmed">
                {formatSize(file.sizeBytes)}
              </Text>
            </Group>
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
