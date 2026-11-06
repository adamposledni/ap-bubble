import { useCallback, useEffect, useState } from 'react';

import { getJson } from '../api/client';

export interface ApiState<T> {
  data: T | undefined;
  /** ISO timestamp of the last successful fetch. */
  updatedAt: string | undefined;
  error: string | undefined;
  loading: boolean;
  reload: () => void;
}

/** GETs path (again whenever it changes, and every refreshMs if given). */
export function useApi<T>(path: string, refreshMs?: number): ApiState<T> {
  const [data, setData] = useState<T>();
  const [updatedAt, setUpdatedAt] = useState<string>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getJson<T>(path, controller.signal)
      .then((result) => {
        setData(result);
        setUpdatedAt(new Date().toISOString());
        setError(undefined);
      })
      .catch((reason: Error) => {
        if (!controller.signal.aborted) setError(reason.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [path, version]);

  useEffect(() => {
    if (!refreshMs) return;
    const timer = setInterval(reload, refreshMs);
    return () => clearInterval(timer);
  }, [refreshMs, reload]);

  return { data, updatedAt, error, loading, reload };
}
