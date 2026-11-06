import { Text, Tooltip } from '@mantine/core';

/** A one-line error; the full text shows on hover. */
export function ErrorText({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <Tooltip label={error} multiline maw={480} withArrow>
      <Text size="xs" c="red" lineClamp={1} maw={320}>
        {error}
      </Text>
    </Tooltip>
  );
}
