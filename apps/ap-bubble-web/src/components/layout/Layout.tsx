import { AppShell, Burger, Group, NavLink, Title } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconActivity,
  IconHelpCircle,
  IconInbox,
  IconLayoutDashboard,
} from '@tabler/icons-react';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router';

const PAGES = [
  { path: '/', label: 'Overview', icon: IconLayoutDashboard },
  { path: '/input', label: 'Input', icon: IconInbox },
  { path: '/questions', label: 'Questions', icon: IconHelpCircle },
  { path: '/monitor', label: 'Monitor', icon: IconActivity },
];

export function Layout({ children }: { children: ReactNode }) {
  const [opened, { toggle, close }] = useDisclosure();
  const { pathname } = useLocation();

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 220, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <Title order={4} c="indigo">
            Adam's bubble
          </Title>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs">
        {PAGES.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            component={Link}
            to={path}
            label={label}
            leftSection={<Icon size={18} stroke={1.5} />}
            active={pathname === path}
            onClick={close}
          />
        ))}
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
