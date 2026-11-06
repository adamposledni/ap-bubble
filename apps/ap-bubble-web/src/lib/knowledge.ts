// Knowledge folders and the in-app paths of knowledge files.

import type { KnowledgeFolder } from '../api/types';

export type FolderFilter = KnowledgeFolder | 'all';

export const FOLDER_LABELS: Record<KnowledgeFolder, string> = {
  people: 'People',
  places: 'Places',
  topics: 'Topics',
  me: 'Me',
};

const FOLDERS = Object.keys(FOLDER_LABELS) as KnowledgeFolder[];
const DOC_LINK = /^\/(people|places|topics|me)\/([^/]+)\.md$/;
const ABSOLUTE = /^([a-z][a-z0-9+.-]*:|\/)/i;
const LINK_BASE = 'http://knowledge.local/';

/** Router state of links to a knowledge file: the search (?q=...) to go back to. */
export interface KnowledgeNavState {
  search: string;
}

export function toFolderFilter(value: string | null): FolderFilter {
  return FOLDERS.find((folder) => folder === value) ?? 'all';
}

export function docPath(folder: KnowledgeFolder, slug: string): string {
  return `/knowledge/${folder}/${encodeURIComponent(slug)}`;
}

/** The detail page a relative link such as '../people/petr-novak.md' in a file of folder points to. */
export function knowledgeLinkPath(folder: KnowledgeFolder, href: string): string | undefined {
  if (ABSOLUTE.test(href)) return undefined;
  try {
    const { pathname } = new URL(href, `${LINK_BASE}${folder}/`);
    const match = DOC_LINK.exec(decodeURIComponent(pathname));
    return match ? docPath(match[1] as KnowledgeFolder, match[2]) : undefined;
  } catch {
    return undefined; // malformed href
  }
}
