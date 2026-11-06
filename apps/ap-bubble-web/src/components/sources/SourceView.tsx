import type { SourceRef } from '../../lib/sources';
import { InputSourceView } from './InputSourceView';
import { ItemRangeView } from './ItemRangeView';
import { ItemSourceView } from './ItemSourceView';

/** A source cited by a knowledge file: an L1 input, an L0 item or a range of L0 items. */
export function SourceView({ source }: { source: SourceRef }) {
  switch (source.type) {
    case 'input':
      return <InputSourceView id={source.id} />;
    case 'item':
      return <ItemSourceView id={source.id} />;
    case 'items':
      return <ItemRangeView from={source.from} to={source.to} />;
  }
}
