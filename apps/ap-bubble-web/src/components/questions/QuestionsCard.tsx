import { Badge, Card, Group, Stack, Title } from '@mantine/core';

import type { Question } from '../../api/types';
import type { ApiState } from '../../hooks/useApi';
import { Loadable } from '../common/Loadable';
import { QuestionItem } from './QuestionItem';

/** Questions the curator could not settle on its own; hidden when there are none. */
export function QuestionsCard({ questions }: { questions: ApiState<Question[]> }) {
  const items = questions.data ?? [];
  if (!questions.error && items.length === 0) return null;

  return (
    <Card withBorder padding="lg">
      <Group justify="space-between" mb="md">
        <Title order={3}>Questions</Title>
        <Badge variant="light">{items.length} open</Badge>
      </Group>
      <Loadable loading={questions.loading} error={questions.error} hasData={questions.data !== undefined}>
        <Stack gap="lg">
          {items.map((question) => (
            <QuestionItem key={question.id} question={question} onDone={questions.reload} />
          ))}
        </Stack>
      </Loadable>
    </Card>
  );
}
