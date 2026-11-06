import { Stack, Text } from '@mantine/core';

import type { ItemDetail } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { sourceApiPath } from '../../lib/sources';
import { Loadable } from '../common/Loadable';
import { ItemHeader } from './ItemHeader';
import { PayloadView } from './PayloadView';
import { SourceText } from './SourceText';

/** One L0 item (l0:N): its header, its text and the raw data behind it. */
export function ItemSourceView({ id }: { id: number }) {
  const { data, error, loading } = useApi<ItemDetail>(sourceApiPath({ type: 'item', id }));

  return (
    <Loadable loading={loading} error={error} hasData={data !== undefined}>
      {data && (
        <Stack gap="md">
          <ItemHeader item={data} />
          {data.text ? (
            <SourceText text={data.text} />
          ) : (
            <Text size="sm" c="dimmed">
              No text; see the raw data.
            </Text>
          )}
          <PayloadView payload={data.payload} />
        </Stack>
      )}
    </Loadable>
  );
}
