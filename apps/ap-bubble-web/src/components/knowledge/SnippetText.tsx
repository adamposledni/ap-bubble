import { Mark, Text } from '@mantine/core';

import type { SnippetPart } from '../../api/types';
import { splitCitations } from '../../lib/citations';
import { Citation } from './Citation';

/** A search snippet with the matched words highlighted and citations dimmed. */
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
          <PlainText key={index} text={part.text} />
        ),
      )}
    </Text>
  );
}

function PlainText({ text }: { text: string }) {
  return splitCitations(text).map((piece, index) =>
    piece.citation ? <Citation key={index}>{piece.text}</Citation> : <span key={index}>{piece.text}</span>,
  );
}
