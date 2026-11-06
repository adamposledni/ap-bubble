import { Anchor, Group, Text } from '@mantine/core';
import { IconPaperclip } from '@tabler/icons-react';

import type { InputFile } from '../../api/types';
import { formatSize } from '../../lib/format';

/** A file of an input: its name as a download link, and its size. */
export function InputFileLink({ file }: { file: InputFile }) {
  return (
    <Group gap={6} wrap="nowrap">
      <IconPaperclip size={14} stroke={1.5} />
      <Anchor href={`/api/inputs/files/${file.id}`} size="sm" truncate>
        {file.name}
      </Anchor>
      <Text size="xs" c="dimmed">
        {formatSize(file.sizeBytes)}
      </Text>
    </Group>
  );
}
