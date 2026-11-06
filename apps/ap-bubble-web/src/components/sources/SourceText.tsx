import { Paper, Text } from '@mantine/core';

/** The text of a source as it was written, line breaks kept. */
export function SourceText({ text }: { text: string }) {
  return (
    <Paper withBorder p="lg">
      <Text size="sm" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
        {text}
      </Text>
    </Paper>
  );
}
