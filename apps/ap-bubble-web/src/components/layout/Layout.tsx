import { Anchor, AppShell, Group, Title } from '@mantine/core';
import type { ReactNode } from 'react';
import { Link } from 'react-router';

/** Header with the app title (back to Overview); no side navigation. */
export function Layout({ children }: { children: ReactNode }) {
  return (
    <AppShell header={{ height: 56 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md">
          <Anchor component={Link} to="/" underline="never">
            <Title order={4} c="indigo">
              Adam's bubble
            </Title>
          </Anchor>
        </Group>
      </AppShell.Header>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
