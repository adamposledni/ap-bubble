import { ActionIcon, Group, Stack, Text } from '@mantine/core';
import { IconPaperclip, IconX } from '@tabler/icons-react';

import { formatSize } from '../../lib/format';

interface Props {
  files: File[];
  onRemove: (index: number) => void;
}

export function SelectedFiles({ files, onRemove }: Props) {
  if (files.length === 0) return null;
  return (
    <Stack gap={4}>
      {files.map((file, index) => (
        <Group key={`${file.name}-${index}`} gap="xs" wrap="nowrap">
          <IconPaperclip size={14} stroke={1.5} />
          <Text size="sm" truncate style={{ flex: 1 }}>
            {file.name}
          </Text>
          <Text size="xs" c="dimmed">
            {formatSize(file.size)}
          </Text>
          <ActionIcon
            variant="subtle"
            color="gray"
            size="sm"
            onClick={() => onRemove(index)}
            aria-label={`Remove ${file.name}`}
          >
            <IconX size={14} />
          </ActionIcon>
        </Group>
      ))}
    </Stack>
  );
}
