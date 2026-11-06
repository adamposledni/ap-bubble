import { ActionIcon, Group, Indicator, Tooltip } from '@mantine/core';
import { IconActivity, IconInbox, IconLayoutDashboard } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router';

import type { Question } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { PAGE_TITLES } from '../../lib/pages';

const QUESTIONS_REFRESH_MS = 60_000;
const ICON_PROPS = { size: 18, stroke: 1.5 };

/** Icon buttons to the other pages; the current page's button is hidden. */
export function NavButtons() {
  const { pathname } = useLocation();
  return (
    <Group gap="xs">
      {pathname !== '/' && (
        <NavButton to="/" label={PAGE_TITLES['/']}>
          <IconLayoutDashboard {...ICON_PROPS} />
        </NavButton>
      )}
      {pathname !== '/input' && <InputButton />}
      {pathname !== '/monitor' && (
        <NavButton to="/monitor" label={PAGE_TITLES['/monitor']}>
          <IconActivity {...ICON_PROPS} />
        </NavButton>
      )}
    </Group>
  );
}

/** Input, with a badge of the open questions waiting there. */
function InputButton() {
  const pending = useApi<Question[]>('/api/questions', QUESTIONS_REFRESH_MS).data?.length ?? 0;
  const title = PAGE_TITLES['/input'];
  const label = pending > 0 ? `${title} · ${pending} open questions` : title;
  return (
    <Indicator label={pending} size={16} disabled={pending === 0}>
      <NavButton to="/input" label={label}>
        <IconInbox {...ICON_PROPS} />
      </NavButton>
    </Indicator>
  );
}

interface NavButtonProps {
  to: string;
  label: string;
  children: ReactNode;
}

function NavButton({ to, label, children }: NavButtonProps) {
  return (
    <Tooltip label={label}>
      <ActionIcon component={Link} to={to} variant="default" size="lg" aria-label={label}>
        {children}
      </ActionIcon>
    </Tooltip>
  );
}
