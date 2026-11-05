import { Badge, Group, Text } from '@mantine/core';
import { IconRepeat } from '@tabler/icons-react';

import type { AgendaEvent } from '../../api/types';
import { addDays, formatShortDay, formatTime } from '../../lib/dates';

export function AgendaEventRow({ event }: { event: AgendaEvent }) {
  return (
    <Group gap="sm" wrap="nowrap" align="flex-start">
      <Text size="sm" c="dimmed" w={100} style={{ flexShrink: 0, whiteSpace: 'nowrap' }}>
        {timeLabel(event)}
      </Text>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Group gap={6} wrap="nowrap">
          <Text size="sm" truncate>
            {event.title || '(no title)'}
          </Text>
          {event.recurring && (
            <IconRepeat size={14} stroke={1.5} color="var(--mantine-color-dimmed)" />
          )}
        </Group>
        {event.location && (
          <Text size="xs" c="dimmed" truncate>
            {event.location}
          </Text>
        )}
      </div>
      {event.calendar && (
        <Badge variant="light" color="gray" size="sm" tt="none" maw={180} style={{ flexShrink: 0 }}>
          {event.calendar}
        </Badge>
      )}
    </Group>
  );
}

function timeLabel(event: AgendaEvent): string {
  if (!event.allDay) {
    return `${formatTime(event.start)} – ${formatTime(event.end)}`;
  }
  const lastDay = addDays(event.end, -1); // the end date is exclusive
  return lastDay === event.start ? 'All day' : `Until ${formatShortDay(lastDay)}`;
}
