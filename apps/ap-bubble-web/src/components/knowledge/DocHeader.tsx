import { Anchor, Group, Stack, Text, Title } from '@mantine/core';
import { IconMail, IconPhone } from '@tabler/icons-react';

import type { KnowledgeDoc } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { FolderBadge } from './FolderBadge';
import { TagList } from './TagList';

/** The front matter of a knowledge file: name, aliases, contacts, tags, updated. */
export function DocHeader({ doc }: { doc: KnowledgeDoc }) {
  const { meta } = doc;
  return (
    <Stack gap="xs">
      <Group gap="sm">
        <Title order={2}>{meta.name}</Title>
        <FolderBadge folder={doc.folder} />
      </Group>
      {meta.aliases.length > 0 && (
        <Text size="sm" c="dimmed">
          Also known as {meta.aliases.join(', ')}
        </Text>
      )}
      <Contacts emails={meta.emails} phones={meta.phones} />
      <Group gap="sm">
        <TagList tags={meta.tags} />
        {meta.updated && (
          <Text size="xs" c="dimmed">
            Updated {formatDate(meta.updated)}
          </Text>
        )}
      </Group>
    </Stack>
  );
}

function Contacts({ emails, phones }: { emails: string[]; phones: string[] }) {
  if (emails.length + phones.length === 0) return null;
  return (
    <Group gap="md">
      {emails.map((email) => (
        <Group key={email} gap={4} wrap="nowrap">
          <IconMail size={16} stroke={1.5} />
          <Anchor href={`mailto:${email}`} size="sm">
            {email}
          </Anchor>
        </Group>
      ))}
      {phones.map((phone) => (
        <Group key={phone} gap={4} wrap="nowrap">
          <IconPhone size={16} stroke={1.5} />
          <Anchor href={`tel:${phone.replace(/\s/g, '')}`} size="sm">
            {phone}
          </Anchor>
        </Group>
      ))}
    </Group>
  );
}
