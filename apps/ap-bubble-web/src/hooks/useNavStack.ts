import { useCallback, useState } from 'react';

export interface NavStack<T> {
  /** The view on top, or null when nothing has been opened. */
  current: T | null;
  depth: number;
  open: (view: T) => void;
  back: () => void;
  reset: () => void;
}

/** A history of opened views: open pushes one, back returns to the one before. */
export function useNavStack<T>(): NavStack<T> {
  const [stack, setStack] = useState<T[]>([]);
  const open = useCallback((view: T) => setStack((views) => [...views, view]), []);
  const back = useCallback(() => setStack((views) => views.slice(0, -1)), []);
  const reset = useCallback(() => setStack([]), []);
  return { current: stack.at(-1) ?? null, depth: stack.length, open, back, reset };
}
