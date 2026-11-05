import { Group, Text } from '@mantine/core';
import { Dropzone } from '@mantine/dropzone';
import { IconUpload } from '@tabler/icons-react';

export function FileDrop({ onDrop }: { onDrop: (files: File[]) => void }) {
  return (
    <Dropzone onDrop={onDrop} multiple p="md">
      <Group justify="center" gap="sm" mih={48} style={{ pointerEvents: 'none' }}>
        <IconUpload size={22} stroke={1.5} color="var(--mantine-color-dimmed)" />
        <Text size="sm" c="dimmed">
          Drop files here or click to choose (documents, images, voice notes, …)
        </Text>
      </Group>
    </Dropzone>
  );
}
