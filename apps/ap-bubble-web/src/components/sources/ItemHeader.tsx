import { Stack, Text, Title } from '@mantine/core';

import type { ItemSummary } from '../../api/types';
import { formatDateOrTime } from '../../lib/dates';
import { ItemBadges } from './ItemBadges';

/** Title, badges, dates and account of an L0 item. */
export function ItemHeader({ item }: { item: ItemSummary }) {
  const when = whenLabel(item);
  return (
    <Stack gap="xs">
      <Title order={3}>{item.title || '(no title)'}</Title>
      <ItemBadges item={item} />
      <Text size="xs" c="dimmed">
        {[when, item.account.email, `l0:${item.id}`].filter(Boolean).join(' · ')}
      </Text>
    </Stack>
  );
}

function whenLabel({ startsAt, endsAt }: ItemSummary): string | undefined {
  if (!startsAt) return undefined;
  const start = formatDateOrTime(startsAt);
  return endsAt ? `${start} – ${formatDateOrTime(endsAt)}` : start;
}
