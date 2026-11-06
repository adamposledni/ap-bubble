import { Grid, Group, Stack } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';

import { AgendaCard } from '../components/agenda/AgendaCard';
import { ContextFilterControl } from '../components/overview/ContextFilterControl';
import { TasksCard } from '../components/tasks/TasksCard';
import type { ContextFilter } from '../lib/context';

/** Basic view straight over L0; it changes once the curated layer exists. */
export function OverviewPage() {
  // Remembered per browser; falls back to 'both' when storage is unavailable.
  const [filter, setFilter] = useLocalStorage<ContextFilter>({
    key: 'overview-context-filter',
    defaultValue: 'both',
  });

  return (
    <Stack gap="md">
      <Group justify="flex-end">
        <ContextFilterControl value={filter} onChange={setFilter} />
      </Group>
      <Grid gutter="md">
        <Grid.Col span={{ base: 12, md: 7 }}>
          <AgendaCard filter={filter} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 5 }}>
          <TasksCard filter={filter} />
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
