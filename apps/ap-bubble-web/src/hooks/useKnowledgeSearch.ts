import { useDebouncedValue } from '@mantine/hooks';
import { useState } from 'react';

import type { KnowledgeSearch } from '../api/types';
import type { FolderFilter } from '../lib/knowledge';
import { useApi } from './useApi';

const DEBOUNCE_MS = 300;

/** Knowledge search state: the text, the folder filter and the debounced API result. */
export function useKnowledgeSearch() {
  const [input, setInput] = useState('');
  const [folder, setFolder] = useState<FolderFilter>('all');
  const [query] = useDebouncedValue(input.trim(), DEBOUNCE_MS);
  const result = useApi<KnowledgeSearch>(`/api/knowledge?${apiParams(query, folder)}`);
  return { input, setInput, folder, setFolder, result };
}

function apiParams(query: string, folder: FolderFilter): URLSearchParams {
  const params = new URLSearchParams({ q: query });
  if (folder !== 'all') params.set('folder', folder);
  return params;
}
