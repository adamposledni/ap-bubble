import { Stack, Text } from '@mantine/core';

import { formatDay, today } from '../../lib/dates';
import { AgendaEventRow } from './AgendaEventRow';
import type { AgendaDay } from './groupByDay';

export function AgendaDayView({ entry }: { entry: AgendaDay }) {
  const isToday = entry.day === today();

  return (
    <div>
      <Text size="sm" fw={600} c={isToday ? 'indigo' : undefined} mb={4}>
        {formatDay(entry.day)}
      </Text>
      {entry.events.length === 0 ? (
        <Text size="sm" c="dimmed">
          No events
        </Text>
      ) : (
        <Stack gap={6}>
          {entry.events.map((event) => (
            <AgendaEventRow key={event.key} event={event} />
          ))}
        </Stack>
      )}
    </div>
  );
}
