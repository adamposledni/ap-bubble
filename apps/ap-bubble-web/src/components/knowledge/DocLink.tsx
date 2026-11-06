import { Anchor } from '@mantine/core';
import type { ReactNode } from 'react';
import { Link } from 'react-router';

import { useOriginSearch } from '../../hooks/useOriginSearch';
import type { KnowledgeNavState } from '../../lib/knowledge';

/** In-app link from one knowledge file to another, keeping the search to go back to. */
export function DocLink({ to, children }: { to: string; children: ReactNode }) {
  const state: KnowledgeNavState = { search: useOriginSearch() };
  return (
    <Anchor component={Link} to={to} state={state}>
      {children}
    </Anchor>
  );
}
