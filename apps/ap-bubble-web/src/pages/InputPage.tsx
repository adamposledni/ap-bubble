import { Stack } from '@mantine/core';
import { useState } from 'react';

import type { InputItem } from '../api/types';
import { InputForm } from '../components/input/InputForm';
import { InputQueue, type QueueView } from '../components/input/InputQueue';
import { useApi } from '../hooks/useApi';

const QUEUE_REFRESH_MS = 10_000; // picks up status changes made by the curator

export function InputPage() {
  const [view, setView] = useState<QueueView>('open');
  const queue = useApi<InputItem[]>(
    view === 'open' ? '/api/inputs?include_done=false' : '/api/inputs',
    QUEUE_REFRESH_MS,
  );

  return (
    <Stack gap="md" maw={900}>
      <InputForm onAdded={queue.reload} />
      <InputQueue queue={queue} view={view} onViewChange={setView} />
    </Stack>
  );
}
