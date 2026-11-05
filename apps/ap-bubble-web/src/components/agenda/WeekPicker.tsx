import { ActionIcon, Button, Group, Text } from '@mantine/core';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';

import { addDays, formatShortDay, today } from '../../lib/dates';

interface Props {
  firstDay: string;
  days: number;
  onChange: (firstDay: string) => void;
}

export function WeekPicker({ firstDay, days, onChange }: Props) {
  const lastDay = addDays(firstDay, days - 1);

  return (
    <Group gap="xs">
      <Text size="sm" c="dimmed" visibleFrom="xs">
        {formatShortDay(firstDay)} – {formatShortDay(lastDay)}
      </Text>
      <ActionIcon
        variant="default"
        onClick={() => onChange(addDays(firstDay, -days))}
        aria-label="Previous days"
      >
        <IconChevronLeft size={16} />
      </ActionIcon>
      <Button variant="default" size="xs" onClick={() => onChange(today())}>
        Today
      </Button>
      <ActionIcon
        variant="default"
        onClick={() => onChange(addDays(firstDay, days))}
        aria-label="Next days"
      >
        <IconChevronRight size={16} />
      </ActionIcon>
    </Group>
  );
}
