import { Mark, Text } from '@mantine/core';

import type { SnippetPart } from '../../api/types';

/** A search snippet with the matched words highlighted. */
export function SnippetText({ parts }: { parts: SnippetPart[] }) {
  if (parts.length === 0) return null;
  return (
    <Text size="sm" c="dimmed" lineClamp={3}>
      {parts.map((part, index) =>
        part.match ? (
          <Mark key={index} color="indigo">
            {part.text}
          </Mark>
        ) : (
          <span key={index}>{part.text}</span>
        ),
      )}
    </Text>
  );
}
