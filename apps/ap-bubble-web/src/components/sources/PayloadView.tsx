import { Button, Code, Collapse, Stack } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';

/** The item as its source delivered it, pretty-printed JSON behind a toggle. */
export function PayloadView({ payload }: { payload: Record<string, unknown> }) {
  const [opened, { toggle }] = useDisclosure(false);
  const Icon = opened ? IconChevronDown : IconChevronRight;

  return (
    <Stack gap="xs" align="flex-start">
      <Button
        variant="subtle"
        size="compact-sm"
        leftSection={<Icon size={16} stroke={1.5} />}
        onClick={toggle}
      >
        Raw data
      </Button>
      <Collapse in={opened} w="100%">
        <Code block style={{ maxHeight: 400, overflow: 'auto' }}>
          {JSON.stringify(payload, null, 2)}
        </Code>
      </Collapse>
    </Stack>
  );
}
