import { ActionIcon, Button, Group, Popover, Text } from '@mantine/core';
import { IconTrash } from '@tabler/icons-react';
import { useState } from 'react';

import { remove } from '../../api/client';

interface Props {
  inputId: number;
  onDeleted: () => void;
}

/** Deletes a still-queued input after a confirmation. */
export function DeleteInputButton({ inputId, onDeleted }: Props) {
  const [opened, setOpened] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string>();

  async function confirm() {
    setDeleting(true);
    setError(undefined);
    try {
      await remove(`/api/inputs/${inputId}`);
      setOpened(false);
      onDeleted();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Popover opened={opened} onChange={setOpened} position="bottom-end" withArrow shadow="md">
      <Popover.Target>
        <ActionIcon
          variant="subtle"
          color="gray"
          onClick={() => setOpened((o) => !o)}
          aria-label="Delete input"
        >
          <IconTrash size={16} />
        </ActionIcon>
      </Popover.Target>
      <Popover.Dropdown>
        <Text size="sm" mb="xs">
          Delete this input?
        </Text>
        {error && (
          <Text size="xs" c="red" mb="xs">
            {error}
          </Text>
        )}
        <Group justify="flex-end" gap="xs">
          <Button size="xs" variant="default" onClick={() => setOpened(false)}>
            Cancel
          </Button>
          <Button size="xs" color="red" loading={deleting} onClick={confirm}>
            Delete
          </Button>
        </Group>
      </Popover.Dropdown>
    </Popover>
  );
}
