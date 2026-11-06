import { Grid, Group, Stack } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';

import { AgendaCard } from '../components/agenda/AgendaCard';
import { KnowledgeSearch } from '../components/knowledge/KnowledgeSearch';
import { ContextFilterControl } from '../components/overview/ContextFilterControl';
import { TasksCard } from '../components/tasks/TasksCard';
import type { ContextFilter } from '../lib/context';

/** Knowledge search and context filter, then agenda and tasks. */
export function OverviewPage() {
  // Remembered per browser; falls back to 'personal' when nothing is stored.
  const [filter, setFilter] = useLocalStorage<ContextFilter>({
    key: 'overview-context-filter',
    defaultValue: 'personal',
  });

  return (
    <Stack gap="md">
      <Group gap="sm">
        <KnowledgeSearch />
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
