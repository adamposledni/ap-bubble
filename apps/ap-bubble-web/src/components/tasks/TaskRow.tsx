import { Badge, Group, Stack, Text } from '@mantine/core';
import { IconCircle } from '@tabler/icons-react';

import type { OpenTask } from '../../api/types';
import { formatShortDay, today } from '../../lib/dates';

export function TaskRow({ task }: { task: OpenTask }) {
  const overdue = task.due !== null && task.due < today();

  return (
    <div>
      <Group gap="xs" wrap="nowrap" align="flex-start">
        <IconCircle
          size={16}
          stroke={1.5}
          color="var(--mantine-color-dimmed)"
          style={{ marginTop: 3, flexShrink: 0 }}
        />
        <div style={{ flex: 1, minWidth: 0 }}>
          <Text size="sm">{task.title || '(no title)'}</Text>
          {task.notes && (
            <Text size="xs" c="dimmed" lineClamp={2}>
              {task.notes}
            </Text>
          )}
        </div>
        {task.due && (
          <Badge size="sm" variant="light" color={overdue ? 'red' : 'gray'} style={{ flexShrink: 0 }}>
            {formatShortDay(task.due)}
          </Badge>
        )}
        {task.listName && (
          <Badge
            size="sm"
            variant="outline"
            color="gray"
            tt="none"
            maw={140}
            style={{ flexShrink: 0 }}
          >
            {task.listName}
          </Badge>
        )}
      </Group>
      {task.subtasks.length > 0 && (
        <Stack gap={4} pl="lg" mt={4}>
          {task.subtasks.map((subtask) => (
            <TaskRow key={subtask.id} task={{ ...subtask, listName: null }} />
          ))}
        </Stack>
      )}
    </div>
  );
}
