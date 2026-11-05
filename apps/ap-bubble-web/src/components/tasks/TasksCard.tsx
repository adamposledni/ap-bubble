import { Badge, Card, Group, Stack, Text, Title } from '@mantine/core';

import type { OpenTask } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { Loadable } from '../common/Loadable';
import { TaskRow } from './TaskRow';

export function TasksCard() {
  const { data, error, loading } = useApi<OpenTask[]>('/api/tasks');
  const tasks = data ?? [];

  return (
    <Card withBorder padding="lg">
      <Group justify="space-between" mb="md">
        <Title order={3}>Tasks</Title>
        <Badge variant="light">{tasks.length} open</Badge>
      </Group>
      <Loadable loading={loading} error={error} hasData={data !== undefined}>
        {tasks.length === 0 ? (
          <Text size="sm" c="dimmed">
            Nothing open.
          </Text>
        ) : (
          <Stack gap="sm">
            {tasks.map((task) => (
              <TaskRow key={task.id} task={task} />
            ))}
          </Stack>
        )}
      </Loadable>
    </Card>
  );
}
