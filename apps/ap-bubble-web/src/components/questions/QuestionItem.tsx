import { Button, Group, Stack, Text, Textarea } from '@mantine/core';
import { getHotkeyHandler } from '@mantine/hooks';
import { useState } from 'react';

import { postJson } from '../../api/client';
import type { Question } from '../../api/types';

/** One open question with an inline answer, or a dismissal. */
export function QuestionItem({ question, onDone }: { question: Question; onDone: () => void }) {
  const [answer, setAnswer] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const base = `/api/questions/${question.id}`;

  async function act(path: string, body?: unknown) {
    setBusy(true);
    setError(undefined);
    try {
      await postJson(path, body);
      onDone();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const submit = () => {
    if (answer.trim() && !busy) void act(`${base}/answer`, { text: answer });
  };

  return (
    <Stack gap="xs">
      <Text size="sm">{question.text}</Text>
      <Textarea
        placeholder="Your answer…"
        autosize
        minRows={1}
        maxRows={8}
        value={answer}
        onChange={(event) => setAnswer(event.currentTarget.value)}
        onKeyDown={getHotkeyHandler([['mod+Enter', submit]])}
      />
      {error && (
        <Text size="xs" c="red">
          {error}
        </Text>
      )}
      <Group justify="flex-end" gap="xs">
        <Button
          size="xs"
          variant="subtle"
          color="gray"
          disabled={busy}
          onClick={() => act(`${base}/dismiss`)}
        >
          Dismiss
        </Button>
        <Button size="xs" loading={busy} disabled={!answer.trim()} onClick={submit}>
          Answer
        </Button>
      </Group>
    </Stack>
  );
}
