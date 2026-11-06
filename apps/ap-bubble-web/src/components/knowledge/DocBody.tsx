import { Anchor, Typography } from '@mantine/core';
import type { ReactNode } from 'react';
import Markdown from 'react-markdown';

import type { KnowledgeFolder } from '../../api/types';
import { knowledgeLinkPath } from '../../lib/knowledge';
import { CITATION_CLASS, rehypeCitations } from '../../lib/rehypeCitations';
import { Citation } from './Citation';
import { DocLink } from './DocLink';

const EXTERNAL = /^(https?:|mailto:|tel:)/i;

/** The markdown body of a knowledge file; links to other files open their pages, citations are dimmed. */
export function DocBody({ folder, body }: { folder: KnowledgeFolder; body: string }) {
  return (
    <Typography>
      <Markdown
        rehypePlugins={[rehypeCitations]}
        components={{
          span: ({ className, children }) =>
            className === CITATION_CLASS ? <Citation>{children}</Citation> : <span>{children}</span>,
          a: ({ href, children }) => (
            <BodyLink folder={folder} href={href ?? ''}>
              {children}
            </BodyLink>
          ),
        }}
      >
        {body}
      </Markdown>
    </Typography>
  );
}

interface BodyLinkProps {
  folder: KnowledgeFolder;
  href: string;
  children: ReactNode;
}

/** Knowledge files in the app, web links in a new tab, anything else as plain text. */
function BodyLink({ folder, href, children }: BodyLinkProps) {
  const path = knowledgeLinkPath(folder, href);
  if (path) return <DocLink to={path}>{children}</DocLink>;
  if (EXTERNAL.test(href)) {
    return (
      <Anchor href={href} target="_blank" rel="noreferrer">
        {children}
      </Anchor>
    );
  }
  return <>{children}</>;
}
