import { Card, Group, Stack, Title } from '@mantine/core';
import { useMemo, useState } from 'react';

import type { AgendaEvent } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { timeZone, today } from '../../lib/dates';
import { Loadable } from '../common/Loadable';
import { AgendaDayView } from './AgendaDayView';
import { groupByDay } from './groupByDay';
import { WeekPicker } from './WeekPicker';

const DAYS = 7;

export function AgendaCard() {
  const [firstDay, setFirstDay] = useState(today);
  const path = `/api/agenda?start=${firstDay}&days=${DAYS}&tz=${encodeURIComponent(timeZone)}`;
  const { data, error, loading } = useApi<AgendaEvent[]>(path);
  const days = useMemo(() => groupByDay(data ?? [], firstDay, DAYS), [data, firstDay]);

  return (
    <Card withBorder padding="lg">
      <Group justify="space-between" mb="md">
        <Title order={3}>Calendar</Title>
        <WeekPicker firstDay={firstDay} days={DAYS} onChange={setFirstDay} />
      </Group>
      <Loadable loading={loading} error={error} hasData={data !== undefined}>
        <Stack gap="md">
          {days.map((entry) => (
            <AgendaDayView key={entry.day} entry={entry} />
          ))}
        </Stack>
      </Loadable>
    </Card>
  );
}
