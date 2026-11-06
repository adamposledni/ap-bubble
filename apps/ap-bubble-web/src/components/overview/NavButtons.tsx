import { ActionIcon, Group, Indicator, Tooltip } from '@mantine/core';
import { IconActivity, IconInbox } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router';

import type { Question } from '../../api/types';
import { useApi } from '../../hooks/useApi';

const QUESTIONS_REFRESH_MS = 60_000;

/** Icon buttons to the Input (with pending questions) and Monitor pages. */
export function NavButtons() {
  return (
    <Group gap="xs">
      <InputButton />
      <NavButton to="/monitor" label="Monitor">
        <IconActivity size={18} stroke={1.5} />
      </NavButton>
    </Group>
  );
}

function InputButton() {
  const pending = useApi<Question[]>('/api/questions', QUESTIONS_REFRESH_MS).data?.length ?? 0;
  const label = pending > 0 ? `Input · ${pending} open questions` : 'Input';
  return (
    <Indicator label={pending} size={16} disabled={pending === 0}>
      <NavButton to="/input" label={label}>
        <IconInbox size={18} stroke={1.5} />
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
