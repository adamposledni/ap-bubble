import { Alert, Center, Loader } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import type { ReactNode } from 'react';

interface Props {
  loading: boolean;
  error: string | undefined;
  hasData: boolean;
  children: ReactNode;
}

/** An error, a loader on first load, else the content (kept visible while reloading). */
export function Loadable({ loading, error, hasData, children }: Props) {
  if (error) {
    return (
      <Alert color="red" icon={<IconAlertCircle size={18} />} title="Could not load">
        {error}
      </Alert>
    );
  }
  if (loading && !hasData) {
    return (
      <Center py="lg">
        <Loader size="sm" />
      </Center>
    );
  }
  return <>{children}</>;
}
