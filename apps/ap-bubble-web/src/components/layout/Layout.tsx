import { Anchor, AppShell, Group, Title } from '@mantine/core';
import type { ReactNode } from 'react';
import { Link } from 'react-router';

import { NavButtons } from './NavButtons';

/** Header with the app title (back to Overview) and icon buttons to the other pages. */
export function Layout({ children }: { children: ReactNode }) {
  return (
    <AppShell header={{ height: 56 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Anchor component={Link} to="/" underline="never">
            <Title order={4} c="indigo">
              Adam's bubble
            </Title>
          </Anchor>
          <NavButtons />
        </Group>
      </AppShell.Header>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
