import { Anchor, Typography } from '@mantine/core';
import type { ReactNode } from 'react';
import Markdown from 'react-markdown';

import type { KnowledgeFolder } from '../../api/types';
import { knowledgeLinkRef } from '../../lib/knowledge';
import { CITATION_CLASS, CITATION_REF_CLASS, rehypeCitations } from '../../lib/rehypeCitations';
import { Citation } from './Citation';
import { CitationLink } from './CitationLink';
import { DocLink } from './DocLink';

const EXTERNAL = /^(https?:|mailto:|tel:)/i;

/** The markdown body of a knowledge file; links open other files, citations open their sources. */
export function DocBody({ folder, body }: { folder: KnowledgeFolder; body: string }) {
  return (
    <Typography>
      <Markdown
        rehypePlugins={[rehypeCitations]}
        components={{
          span: ({ className, children }) => <BodySpan className={className}>{children}</BodySpan>,
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

/** Citations are dimmed; each source reference in one is a link. */
function BodySpan({ className, children }: { className: string | undefined; children: ReactNode }) {
  if (className === CITATION_CLASS) return <Citation>{children}</Citation>;
  if (className === CITATION_REF_CLASS) return <CitationLink text={String(children)} />;
  return <span>{children}</span>;
}

interface BodyLinkProps {
  folder: KnowledgeFolder;
  href: string;
  children: ReactNode;
}

/** Knowledge files in the dialog, web links in a new tab, anything else as plain text. */
function BodyLink({ folder, href, children }: BodyLinkProps) {
  const doc = knowledgeLinkRef(folder, href);
  if (doc) return <DocLink doc={doc}>{children}</DocLink>;
  if (EXTERNAL.test(href)) {
    return (
      <Anchor href={href} target="_blank" rel="noreferrer">
        {children}
      </Anchor>
    );
  }
  return <>{children}</>;
}
