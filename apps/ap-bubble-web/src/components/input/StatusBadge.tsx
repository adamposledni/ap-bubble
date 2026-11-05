import { Badge } from '@mantine/core';

import type { InputStatus } from '../../api/types';

const COLORS: Record<InputStatus, string> = {
  queued: 'gray',
  processing: 'indigo',
  done: 'green',
  failed: 'red',
};

export function StatusBadge({ status }: { status: InputStatus }) {
  return (
    <Badge size="sm" variant="light" color={COLORS[status]}>
      {status}
    </Badge>
  );
}
