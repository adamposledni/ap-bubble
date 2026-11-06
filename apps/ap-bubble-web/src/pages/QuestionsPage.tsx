import { Badge, Card, Group, Stack, Text, Title } from '@mantine/core';

import type { Question } from '../api/types';
import { Loadable } from '../components/common/Loadable';
import { QuestionItem } from '../components/questions/QuestionItem';
import { useApi } from '../hooks/useApi';

/** Questions the curator could not settle on its own; answering one queues an input. */
export function QuestionsPage() {
  const questions = useApi<Question[]>('/api/questions');
  const items = questions.data ?? [];

  return (
    <Stack gap="md" maw={900}>
      <Card withBorder padding="lg">
        <Group justify="space-between" mb="md">
          <Title order={3}>Questions</Title>
          <Badge variant="light">{items.length} open</Badge>
        </Group>
        <Loadable
          loading={questions.loading}
          error={questions.error}
          hasData={questions.data !== undefined}
        >
          {items.length === 0 ? (
            <Text size="sm" c="dimmed">
              No open questions.
            </Text>
          ) : (
            <Stack gap="lg">
              {items.map((question) => (
                <QuestionItem key={question.id} question={question} onDone={questions.reload} />
              ))}
            </Stack>
          )}
        </Loadable>
      </Card>
    </Stack>
  );
}
