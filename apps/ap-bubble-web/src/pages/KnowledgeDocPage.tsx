import { Paper, Stack } from '@mantine/core';
import { useParams } from 'react-router';

import type { KnowledgeDoc } from '../api/types';
import { Loadable } from '../components/common/Loadable';
import { Backlinks } from '../components/knowledge/Backlinks';
import { BackToSearch } from '../components/knowledge/BackToSearch';
import { DocBody } from '../components/knowledge/DocBody';
import { DocHeader } from '../components/knowledge/DocHeader';
import { useApi } from '../hooks/useApi';

/** One knowledge file: its front matter, markdown body and the files mentioning it. */
export function KnowledgeDocPage() {
  const { folder = '', slug = '' } = useParams();
  const path = `/api/knowledge/${encodeURIComponent(folder)}/${encodeURIComponent(slug)}`;
  const { data, error, loading } = useApi<KnowledgeDoc>(path);

  return (
    <Stack gap="md" maw={900}>
      <BackToSearch />
      <Loadable loading={loading} error={error} hasData={data !== undefined}>
        {data && (
          <Stack gap="md">
            <DocHeader doc={data} />
            <Paper withBorder p="lg">
              <DocBody folder={data.folder} body={data.body} />
            </Paper>
            <Backlinks refs={data.backlinks} />
          </Stack>
        )}
      </Loadable>
    </Stack>
  );
}
