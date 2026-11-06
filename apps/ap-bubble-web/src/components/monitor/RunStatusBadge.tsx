import { Badge } from '@mantine/core';

import type { RunStatus } from '../../api/types';

const COLORS: Record<RunStatus, string> = {
  running: 'indigo',
  succeeded: 'green',
  failed: 'red',
};

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return (
    <Badge size="sm" variant="light" color={COLORS[status]}>
      {status}
    </Badge>
  );
}
