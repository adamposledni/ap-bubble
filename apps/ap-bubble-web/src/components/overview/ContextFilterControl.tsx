import { SegmentedControl } from '@mantine/core';

import type { ContextFilter } from '../../lib/context';

const OPTIONS: { label: string; value: ContextFilter }[] = [
  { label: 'Both', value: 'both' },
  { label: 'Work', value: 'work' },
  { label: 'Personal', value: 'personal' },
];

interface Props {
  value: ContextFilter;
  onChange: (value: ContextFilter) => void;
}

export function ContextFilterControl({ value, onChange }: Props) {
  return (
    <SegmentedControl
      size="sm"
      data={OPTIONS}
      value={value}
      onChange={(next) => onChange(next as ContextFilter)}
      aria-label="Show work, personal or both"
    />
  );
}
