import { Alert, Button, Card, Group, Stack, Text, Textarea, Title } from '@mantine/core';
import { getHotkeyHandler } from '@mantine/hooks';
import { IconSend } from '@tabler/icons-react';
import { useState } from 'react';

import { postForm } from '../../api/client';
import { FileDrop } from './FileDrop';
import { SelectedFiles } from './SelectedFiles';

/** One input: an optional text plus any number of files, queued for the curator. */
export function InputForm({ onAdded }: { onAdded: () => void }) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string>();
  const canSend = (text.trim() !== '' || files.length > 0) && !sending;

  async function submit() {
    if (!canSend) return;
    const form = new FormData();
    if (text.trim()) form.append('text', text);
    files.forEach((file) => form.append('files', file));
    setSending(true);
    setError(undefined);
    try {
      await postForm('/api/inputs', form);
      setText('');
      setFiles([]);
      onAdded();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setSending(false);
    }
  }

  return (
    <Card withBorder padding="lg">
      <Title order={3} mb="md">
        New input
      </Title>
      <Stack gap="sm">
        <Textarea
          placeholder="A note, a fact, a correction, an idea…"
          autosize
          minRows={3}
          maxRows={12}
          value={text}
          onChange={(event) => setText(event.currentTarget.value)}
          onKeyDown={getHotkeyHandler([['mod+Enter', submit]])}
        />
        <FileDrop onDrop={(dropped) => setFiles((current) => [...current, ...dropped])} />
        <SelectedFiles
          files={files}
          onRemove={(index) => setFiles((current) => current.filter((_, i) => i !== index))}
        />
        {error && <Alert color="red">{error}</Alert>}
        <Group justify="space-between">
          <Text size="xs" c="dimmed">
            Ctrl+Enter to add
          </Text>
          <Button
            onClick={submit}
            loading={sending}
            disabled={!canSend}
            leftSection={<IconSend size={16} />}
          >
            Add to queue
          </Button>
        </Group>
      </Stack>
    </Card>
  );
}
