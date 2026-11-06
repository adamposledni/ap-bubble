// Rehype plugin: wraps citations in markdown text into <span class="citation"> elements.

import { splitCitations } from './citations';

export const CITATION_CLASS = 'citation';

interface HastText {
  type: 'text';
  value: string;
}

interface HastParent {
  type: string;
  tagName?: string;
  children?: HastNode[];
}

type HastNode = HastText | HastParent;

const SKIPPED_TAGS = new Set(['code', 'pre']);

function citationElement(value: string): HastParent {
  return {
    type: 'element',
    tagName: 'span',
    properties: { className: [CITATION_CLASS] },
    children: [{ type: 'text', value }],
  } as HastParent;
}

function splitText(node: HastText): HastNode[] {
  return splitCitations(node.value).map((piece) =>
    piece.citation ? citationElement(piece.text) : { type: 'text', value: piece.text },
  );
}

function transform(node: HastParent): void {
  if (!node.children || (node.tagName && SKIPPED_TAGS.has(node.tagName))) return;
  node.children = node.children.flatMap((child) => {
    if (child.type === 'text') return splitText(child as HastText);
    transform(child as HastParent);
    return [child];
  });
}

export function rehypeCitations() {
  return (tree: HastParent) => transform(tree);
}
