import type { ReactNode } from 'react';

import { ScrollCard } from '../common/ScrollCard';

/** Header, summary bar, card header and paddings; keeps both lists inside one screen. */
const LIST_MAX_HEIGHT = 'calc(100dvh - 210px)';

interface Props {
  header: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}

/** A monitor list card sized to fit under the summary bar. */
export function MonitorCard(props: Props) {
  return <ScrollCard {...props} maxHeight={LIST_MAX_HEIGHT} />;
}
