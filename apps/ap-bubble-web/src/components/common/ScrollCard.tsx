import { Card, Group, ScrollArea } from '@mantine/core';
import type { ReactNode } from 'react';

/** Header, page paddings and card header; keeps a page's lists inside one screen. */
export const PAGE_LIST_MAX_HEIGHT = 'calc(100dvh - 160px)';

interface Props {
  header: ReactNode;
  actions?: ReactNode;
  /** CSS max height of the scrolling body, e.g. calc(100dvh - 200px). */
  maxHeight: string;
  children: ReactNode;
}

/** A compact card whose body scrolls on its own instead of the page. */
export function ScrollCard({ header, actions, maxHeight, children }: Props) {
  return (
    <Card withBorder padding="sm" h="100%">
      <Group justify="space-between" mb="xs" gap="xs" wrap="nowrap">
        {header}
        {actions}
      </Group>
      <ScrollArea.Autosize mah={maxHeight} type="auto" offsetScrollbars>
        {children}
      </ScrollArea.Autosize>
    </Card>
  );
}
