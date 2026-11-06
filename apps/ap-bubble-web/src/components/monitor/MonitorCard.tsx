import { Card, Group, ScrollArea } from '@mantine/core';
import type { ReactNode } from 'react';

/** Header, summary bar, card header and paddings; keeps both lists inside one screen. */
const LIST_MAX_HEIGHT = 'calc(100dvh - 210px)';

interface Props {
  header: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}

/** A compact card whose body scrolls on its own instead of the page. */
export function MonitorCard({ header, actions, children }: Props) {
  return (
    <Card withBorder padding="sm" h="100%">
      <Group justify="space-between" mb="xs" gap="xs" wrap="nowrap">
        {header}
        {actions}
      </Group>
      <ScrollArea.Autosize mah={LIST_MAX_HEIGHT} type="auto" offsetScrollbars>
        {children}
      </ScrollArea.Autosize>
    </Card>
  );
}
