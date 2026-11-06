import { ActionIcon, Group, Text } from '@mantine/core';
import { IconRefresh } from '@tabler/icons-react';

import { formatDateTime, formatTime } from '../../lib/dates';

interface Props {
  loading: boolean;
  updatedAt: string | undefined;
  onRefresh: () => void;
}

/** When the data last arrived, and a button to fetch it again now. */
export function RefreshControl({ loading, updatedAt, onRefresh }: Props) {
  return (
    <Group gap="xs">
      {updatedAt && (
        <Text size="xs" c="dimmed" title={formatDateTime(updatedAt)}>
          Updated {formatTime(updatedAt)}
        </Text>
      )}
      <ActionIcon variant="default" loading={loading} onClick={onRefresh} aria-label="Refresh">
        <IconRefresh size={16} />
      </ActionIcon>
    </Group>
  );
}
