// Source citations the curator writes into knowledge files: input:7, l0:123, l0:504–519.

import { parseSourceRef, type SourceRef } from './sources';

export interface TextPiece {
  text: string;
  citation: boolean;
}

/** A piece of one citation: a reference to a source, or the parentheses, commas and dates around it. */
export interface CitationPart {
  text: string;
  source: SourceRef | undefined;
}

const REF = String.raw`(?:input|l0):\d+(?:[–-]\d+)?`;
const DATE = String.raw`\d{4}-\d{2}-\d{2}`;
/** A parenthesised group of only citations (and dates), e.g. "(input:4, input:6)" or "(l0:12, 2026-10-02)". */
const GROUP = String.raw`\((?:${DATE},\s*)*${REF}(?:,\s*(?:${REF}|${DATE}))*\)`;
const CITATION = new RegExp(`${GROUP}|${REF}`, 'g');
const REFS = new RegExp(REF, 'g');

/** Splits text into plain pieces and citation pieces (whole groups when they hold only citations). */
export function splitCitations(text: string): TextPiece[] {
  return splitBy(text, CITATION).map(({ text, matched }) => ({ text, citation: matched }));
}

/** Splits one citation (a reference or a whole group) into its references and the text between them. */
export function splitCitation(citation: string): CitationPart[] {
  return splitBy(citation, REFS).map(({ text, matched }) => ({
    text,
    source: matched ? parseSourceRef(text) : undefined,
  }));
}

function splitBy(text: string, pattern: RegExp): { text: string; matched: boolean }[] {
  const pieces: { text: string; matched: boolean }[] = [];
  let last = 0;
  for (const match of text.matchAll(pattern)) {
    const start = match.index;
    if (start > last) pieces.push({ text: text.slice(last, start), matched: false });
    pieces.push({ text: match[0], matched: true });
    last = start + match[0].length;
  }
  if (last < text.length) pieces.push({ text: text.slice(last), matched: false });
  return pieces;
}
