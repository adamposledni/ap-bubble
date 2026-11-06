/** Page names by route, shown in the header and on the nav buttons. */
export const PAGE_TITLES: Record<string, string> = {
  '/': 'Overview',
  '/input': 'Input',
  '/monitor': 'Monitor',
};

export function pageTitle(pathname: string): string | undefined {
  return PAGE_TITLES[pathname];
}
