import { Paper, Stack } from '@mantine/core';

import type { KnowledgeDoc } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { docApiPath, type DocRef } from '../../lib/knowledge';
import { Loadable } from '../common/Loadable';
import { Backlinks } from './Backlinks';
import { DocBody } from './DocBody';
import { DocHeader } from './DocHeader';

/** One knowledge file: its front matter, markdown body and the files mentioning it. */
export function KnowledgeDocView({ doc }: { doc: DocRef }) {
  const { data, error, loading } = useApi<KnowledgeDoc>(docApiPath(doc));

  return (
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
  );
}
