import { Badge, Stack, Title } from '@mantine/core';

import type { Question } from '../../api/types';
import type { ApiState } from '../../hooks/useApi';
import { Loadable } from '../common/Loadable';
import { PAGE_LIST_MAX_HEIGHT, ScrollCard } from '../common/ScrollCard';
import { QuestionItem } from './QuestionItem';

/** Questions the curator could not settle on its own. */
export function QuestionsCard({ questions }: { questions: ApiState<Question[]> }) {
  const items = questions.data ?? [];

  return (
    <ScrollCard
      maxHeight={PAGE_LIST_MAX_HEIGHT}
      header={<Title order={4}>Questions</Title>}
      actions={<Badge variant="light">{items.length} open</Badge>}
    >
      <Loadable loading={questions.loading} error={questions.error} hasData={questions.data !== undefined}>
        <Stack gap="lg">
          {items.map((question) => (
            <QuestionItem key={question.id} question={question} onDone={questions.reload} />
          ))}
        </Stack>
      </Loadable>
    </ScrollCard>
  );
}
