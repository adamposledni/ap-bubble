// Knowledge folders and references to knowledge files.

import type { KnowledgeFolder } from '../api/types';

export type FolderFilter = KnowledgeFolder | 'all';

export const FOLDER_LABELS: Record<KnowledgeFolder, string> = {
  people: 'People',
  places: 'Places',
  topics: 'Topics',
  me: 'Me',
};

/** Identifies one knowledge file. */
export interface DocRef {
  folder: KnowledgeFolder;
  slug: string;
}

const DOC_LINK = /^\/(people|places|topics|me)\/([^/]+)\.md$/;
const ABSOLUTE = /^([a-z][a-z0-9+.-]*:|\/)/i;
const LINK_BASE = 'http://knowledge.local/';

export function docApiPath({ folder, slug }: DocRef): string {
  return `/api/knowledge/${encodeURIComponent(folder)}/${encodeURIComponent(slug)}`;
}

/** The file a relative link such as '../people/petr-novak.md' in a file of folder points to. */
export function knowledgeLinkRef(folder: KnowledgeFolder, href: string): DocRef | undefined {
  if (ABSOLUTE.test(href)) return undefined;
  try {
    const { pathname } = new URL(href, `${LINK_BASE}${folder}/`);
    const match = DOC_LINK.exec(decodeURIComponent(pathname));
    return match ? { folder: match[1] as KnowledgeFolder, slug: match[2] } : undefined;
  } catch {
    return undefined; // malformed href
  }
}
