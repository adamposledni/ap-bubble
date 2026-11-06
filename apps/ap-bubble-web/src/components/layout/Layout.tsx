import { Anchor, AppShell, Group, Text, Title } from '@mantine/core';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router';

import { pageTitle } from '../../lib/pages';
import { NavButtons } from './NavButtons';

/** Header with the app title (back to Overview), the current page's title and nav buttons. */
export function Layout({ children }: { children: ReactNode }) {
  return (
    <AppShell header={{ height: 56 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <HeaderTitle />
          <NavButtons />
        </Group>
      </AppShell.Header>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}

/** "Adam's bubble | <page>"; the app name links back to Overview. */
function HeaderTitle() {
  const page = pageTitle(useLocation().pathname);
  return (
    <Group gap="xs" wrap="nowrap">
      <Anchor component={Link} to="/" underline="never">
        <Title order={4} c="indigo">
          Adam's bubble
        </Title>
      </Anchor>
      {page && (
        <>
          <Text c="dimmed" fw={300}>
            |
          </Text>
          <Title order={4} fw={500}>
            {page}
          </Title>
        </>
      )}
    </Group>
  );
}
