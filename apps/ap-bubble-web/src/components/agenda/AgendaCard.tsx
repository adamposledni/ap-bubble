import { Card, Group, Stack, Title } from '@mantine/core';
import { useMemo, useState } from 'react';

import type { AgendaEvent } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { type ContextFilter, matchesContext } from '../../lib/context';
import { timeZone, today } from '../../lib/dates';
import { Loadable } from '../common/Loadable';
import { AgendaDayView } from './AgendaDayView';
import { groupByDay } from './groupByDay';
import { WeekPicker } from './WeekPicker';

/** Today and tomorrow. */
const DAYS = 2;

export function AgendaCard({ filter }: { filter: ContextFilter }) {
  const [firstDay, setFirstDay] = useState(today);
  const path = `/api/agenda?start=${firstDay}&days=${DAYS}&tz=${encodeURIComponent(timeZone)}`;
  const { data, error, loading } = useApi<AgendaEvent[]>(path);
  const days = useMemo(() => {
    const events = (data ?? []).filter((event) => matchesContext(event.context, filter));
    return groupByDay(events, firstDay, DAYS);
  }, [data, filter, firstDay]);

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
