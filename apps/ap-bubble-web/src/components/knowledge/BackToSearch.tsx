import { Anchor, Group } from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';
import { Link } from 'react-router';

import { useOriginSearch } from '../../hooks/useOriginSearch';

export function BackToSearch() {
  return (
    <Anchor component={Link} to={`/knowledge${useOriginSearch()}`} size="sm">
      <Group gap={4}>
        <IconArrowLeft size={16} stroke={1.5} />
        Knowledge search
      </Group>
    </Anchor>
  );
}
