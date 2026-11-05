import { Grid } from '@mantine/core';

import { AgendaCard } from '../components/agenda/AgendaCard';
import { TasksCard } from '../components/tasks/TasksCard';

/** Basic view straight over L0; it changes once the curated layer exists. */
export function OverviewPage() {
  return (
    <Grid gutter="md">
      <Grid.Col span={{ base: 12, md: 7 }}>
        <AgendaCard />
      </Grid.Col>
      <Grid.Col span={{ base: 12, md: 5 }}>
        <TasksCard />
      </Grid.Col>
    </Grid>
  );
}
