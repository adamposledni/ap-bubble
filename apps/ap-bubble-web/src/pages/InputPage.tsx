import { Stack } from '@mantine/core';

import type { InputItem } from '../api/types';
import { InputForm } from '../components/input/InputForm';
import { InputQueue } from '../components/input/InputQueue';
import { useApi } from '../hooks/useApi';

const QUEUE_REFRESH_MS = 10_000; // picks up status changes made by the curator

export function InputPage() {
  const queue = useApi<InputItem[]>('/api/inputs', QUEUE_REFRESH_MS);

  return (
    <Stack gap="md" maw={900}>
      <InputForm onAdded={queue.reload} />
      <InputQueue queue={queue} />
    </Stack>
  );
}
