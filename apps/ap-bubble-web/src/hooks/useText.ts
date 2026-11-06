import { useEffect, useState } from 'react';

export interface TextState {
  text: string | undefined;
  error: string | undefined;
}

/** GETs a plain-text resource once per path. */
export function useText(path: string): TextState {
  const [state, setState] = useState<TextState>({ text: undefined, error: undefined });

  useEffect(() => {
    const controller = new AbortController();
    setState({ text: undefined, error: undefined });
    fetch(path, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Request failed (${response.status})`);
        return response.text();
      })
      .then((text) => setState({ text, error: undefined }))
      .catch((reason: Error) => {
        if (!controller.signal.aborted) setState({ text: undefined, error: reason.message });
      });
    return () => controller.abort();
  }, [path]);

  return state;
}
