import { Badge } from '@mantine/core';

import type { KnowledgeFolder } from '../../api/types';
import { FOLDER_LABELS } from '../../lib/knowledge';

export function FolderBadge({ folder }: { folder: KnowledgeFolder }) {
  return (
    <Badge variant="light" size="sm">
      {FOLDER_LABELS[folder]}
    </Badge>
  );
}
