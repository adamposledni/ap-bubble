import { Stack } from '@mantine/core';
import { useState } from 'react';

import type { InputItem, Question } from '../api/types';
import { InputForm } from '../components/input/InputForm';
import { InputQueue, type QueueView } from '../components/input/InputQueue';
import { QuestionsCard } from '../components/questions/QuestionsCard';
import { useApi } from '../hooks/useApi';

const QUEUE_REFRESH_MS = 10_000; // picks up status changes made by the curator

/** Open questions of the curator, then the input form and queue (answers become inputs). */
export function InputPage() {
  const [view, setView] = useState<QueueView>('open');
  const queue = useApi<InputItem[]>(
    view === 'open' ? '/api/inputs?include_done=false' : '/api/inputs',
    QUEUE_REFRESH_MS,
  );
  const questions = useApi<Question[]>('/api/questions');

  const onAnswered = () => {
    questions.reload();
    queue.reload();
  };

  return (
    <Stack gap="md" maw={900}>
      <QuestionsCard questions={{ ...questions, reload: onAnswered }} />
      <InputForm onAdded={queue.reload} />
      <InputQueue queue={queue} view={view} onViewChange={setView} />
    </Stack>
  );
}
