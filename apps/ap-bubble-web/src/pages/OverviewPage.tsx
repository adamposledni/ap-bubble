import { Grid, Group, Stack } from '@mantine/core';
import { useState } from 'react';

import { AgendaCard } from '../components/agenda/AgendaCard';
import { KnowledgeSearch } from '../components/knowledge/KnowledgeSearch';
import { ContextFilterControl } from '../components/overview/ContextFilterControl';
import { TasksCard } from '../components/tasks/TasksCard';
import type { ContextFilter } from '../lib/context';

/** Knowledge search and context filter, then agenda and tasks. */
export function OverviewPage() {
  // Always opens on 'personal'; not remembered across visits.
  const [filter, setFilter] = useState<ContextFilter>('personal');

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
