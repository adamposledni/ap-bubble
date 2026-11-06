import { CloseButton, Group, SegmentedControl, TextInput } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';

import { FOLDER_LABELS, type FolderFilter } from '../../lib/knowledge';

const FOLDER_OPTIONS = [
  { value: 'all', label: 'All' },
  ...Object.entries(FOLDER_LABELS).map(([value, label]) => ({ value, label })),
];

interface Props {
  input: string;
  onInput: (value: string) => void;
  folder: FolderFilter;
  onFolder: (value: FolderFilter) => void;
}

export function KnowledgeSearchBar({ input, onInput, folder, onFolder }: Props) {
  return (
    <Group gap="sm" align="center">
      <TextInput
        style={{ flex: 1, minWidth: 220 }}
        placeholder="Search names, tags, emails and text"
        leftSection={<IconSearch size={16} stroke={1.5} />}
        rightSection={input && <CloseButton aria-label="Clear" onClick={() => onInput('')} />}
        value={input}
        onChange={(event) => onInput(event.currentTarget.value)}
        autoFocus
      />
      <SegmentedControl
        data={FOLDER_OPTIONS}
        value={folder}
        onChange={(value) => onFolder(value as FolderFilter)}
      />
    </Group>
  );
}
