import { Grid } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useState } from 'react';

import type { InputItem, Question } from '../api/types';
import { InputQueue, type QueueView } from '../components/input/InputQueue';
import { NewInputDialog } from '../components/input/NewInputDialog';
import { QuestionsCard } from '../components/questions/QuestionsCard';
import { useApi } from '../hooks/useApi';

const QUEUE_REFRESH_MS = 10_000; // picks up status changes made by the curator

/** The input queue (new inputs via a dialog) beside the curator's open questions (answers become inputs). */
export function InputPage() {
  const [view, setView] = useState<QueueView>('open');
  const [dialogOpened, dialog] = useDisclosure(false);
  const queue = useApi<InputItem[]>(
    view === 'open' ? '/api/inputs?include_done=false' : '/api/inputs',
    QUEUE_REFRESH_MS,
  );
  const questions = useApi<Question[]>('/api/questions');
  const showQuestions = Boolean(questions.error) || (questions.data?.length ?? 0) > 0;

  const onAnswered = () => {
    questions.reload();
    queue.reload();
  };

  return (
    <>
      <Grid gutter="sm">
        <Grid.Col span={{ base: 12, lg: showQuestions ? 7 : 12 }}>
          <InputQueue queue={queue} view={view} onViewChange={setView} onNewInput={dialog.open} />
        </Grid.Col>
        {showQuestions && (
          <Grid.Col span={{ base: 12, lg: 5 }}>
            <QuestionsCard questions={{ ...questions, reload: onAnswered }} />
          </Grid.Col>
        )}
      </Grid>
      <NewInputDialog opened={dialogOpened} onClose={dialog.close} onAdded={queue.reload} />
    </>
  );
}
