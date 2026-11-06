// Rehype plugin: wraps citations in markdown text into <span class="citation"> elements,
// each source reference inside them into a <span class="citation-ref">.

import { splitCitation, splitCitations } from './citations';

export const CITATION_CLASS = 'citation';
export const CITATION_REF_CLASS = 'citation-ref';

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

function span(className: string, children: HastNode[]): HastParent {
  return {
    type: 'element',
    tagName: 'span',
    properties: { className: [className] },
    children,
  } as HastParent;
}

function textNode(value: string): HastText {
  return { type: 'text', value };
}

function citationElement(value: string): HastParent {
  const children = splitCitation(value).map((part) =>
    part.source ? span(CITATION_REF_CLASS, [textNode(part.text)]) : textNode(part.text),
  );
  return span(CITATION_CLASS, children);
}

function splitText(node: HastText): HastNode[] {
  return splitCitations(node.value).map((piece) =>
    piece.citation ? citationElement(piece.text) : textNode(piece.text),
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
