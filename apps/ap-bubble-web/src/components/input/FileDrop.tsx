import { Group, Text } from '@mantine/core';
import { Dropzone } from '@mantine/dropzone';
import { IconUpload } from '@tabler/icons-react';

export function FileDrop({ onDrop }: { onDrop: (files: File[]) => void }) {
  return (
    <Dropzone onDrop={onDrop} multiple px="md" py="xs">
      <Group justify="center" gap="xs" style={{ pointerEvents: 'none' }}>
        <IconUpload size={16} stroke={1.5} color="var(--mantine-color-dimmed)" />
        <Text size="xs" c="dimmed">
          Drop files here or click to choose
        </Text>
      </Group>
    </Dropzone>
  );
}
