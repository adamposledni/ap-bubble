import { useDebouncedValue } from '@mantine/hooks';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';

import type { KnowledgeSearch } from '../api/types';
import { type FolderFilter, toFolderFilter } from '../lib/knowledge';
import { useApi } from './useApi';

const DEBOUNCE_MS = 300;

/** Knowledge search kept in the URL (?q=&folder=), so going back restores it. */
export function useKnowledgeSearch() {
  const [params, setParams] = useSearchParams();
  const query = params.get('q') ?? '';
  const folder = toFolderFilter(params.get('folder'));
  const [input, setInput] = useState(query);
  const [debounced] = useDebouncedValue(input.trim(), DEBOUNCE_MS);

  const setParam = (key: string, value: string) =>
    setParams((current) => withParam(current, key, value), { replace: true });

  // Typing updates the URL (debounced); a URL changed elsewhere (nav link) updates the input.
  useEffect(() => {
    if (debounced !== query) setParam('q', debounced);
  }, [debounced]);
  useEffect(() => {
    if (query !== debounced) setInput(query);
  }, [query]);

  const setFolder = (value: FolderFilter) => setParam('folder', value === 'all' ? '' : value);
  const result = useApi<KnowledgeSearch>(`/api/knowledge?${apiParams(query, folder)}`);
  return { input, setInput, folder, setFolder, result };
}

function withParam(current: URLSearchParams, key: string, value: string): URLSearchParams {
  const next = new URLSearchParams(current);
  if (value) next.set(key, value);
  else next.delete(key);
  return next;
}

function apiParams(query: string, folder: FolderFilter): URLSearchParams {
  const params = new URLSearchParams({ q: query });
  if (folder !== 'all') params.set('folder', folder);
  return params;
}
