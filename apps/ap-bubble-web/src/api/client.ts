// Thin fetch wrappers for the local API; errors carry the API's `detail` message.

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  return parse<T>(await fetch(path, { signal }));
}

export async function postForm<T>(path: string, body: FormData): Promise<T> {
  return parse<T>(await fetch(path, { method: 'POST', body }));
}

export async function remove(path: string): Promise<void> {
  await parse<void>(await fetch(path, { method: 'DELETE' }));
}

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const { detail } = await response.json();
    return typeof detail === 'string' ? detail : `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}
