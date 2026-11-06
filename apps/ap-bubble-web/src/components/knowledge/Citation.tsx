import { Text } from '@mantine/core';
import type { ReactNode } from 'react';

/** A source citation (input:7, l0:123): small and dimmed, set apart from the text. */
export function Citation({ children }: { children: ReactNode }) {
  return (
    <Text span fz="xs" fw={400} fs="normal" c="dimmed" ff="monospace" style={{ whiteSpace: 'nowrap' }}>
      {children}
    </Text>
  );
}
