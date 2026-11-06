import { Group, Stack, Text, Title } from '@mantine/core';

import type { InputItem } from '../../api/types';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { sourceApiPath } from '../../lib/sources';
import { Loadable } from '../common/Loadable';
import { InputFileLink } from '../input/InputFileLink';
import { StatusBadge } from '../input/StatusBadge';
import { SourceText } from './SourceText';

/** One of my inputs (input:N): its text, files, status and dates. */
export function InputSourceView({ id }: { id: number }) {
  const { data, error, loading } = useApi<InputItem>(sourceApiPath({ type: 'input', id }));

  return (
    <Loadable loading={loading} error={error} hasData={data !== undefined}>
      {data && (
        <Stack gap="md">
          <Stack gap="xs">
            <Group gap="sm">
              <Title order={3}>Input {data.id}</Title>
              <StatusBadge status={data.status} />
            </Group>
            <Text size="xs" c="dimmed">
              Added {formatDateTime(data.createdAt)}
              {data.processedAt && ` · processed ${formatDateTime(data.processedAt)}`}
            </Text>
          </Stack>
          {data.text && <SourceText text={data.text} />}
          {data.files.map((file) => (
            <InputFileLink key={file.id} file={file} />
          ))}
          {data.error && (
            <Text size="xs" c="red">
              {data.error}
            </Text>
          )}
        </Stack>
      )}
    </Loadable>
  );
}
