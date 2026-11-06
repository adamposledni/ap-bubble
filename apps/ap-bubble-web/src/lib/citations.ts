// Source citations the curator writes into knowledge files: input:7, l0:123, l0:504–519.

export interface TextPiece {
  text: string;
  citation: boolean;
}

const REF = String.raw`(?:input|l0):\d+(?:[–-]\d+)?`;
const DATE = String.raw`\d{4}-\d{2}-\d{2}`;
/** A parenthesised group of only citations (and dates), e.g. "(input:4, input:6)" or "(l0:12, 2026-10-02)". */
const GROUP = String.raw`\((?:${DATE},\s*)*${REF}(?:,\s*(?:${REF}|${DATE}))*\)`;
const CITATION = new RegExp(`${GROUP}|${REF}`, 'g');

/** Splits text into plain pieces and citation pieces (whole groups when they hold only citations). */
export function splitCitations(text: string): TextPiece[] {
  const pieces: TextPiece[] = [];
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    const start = match.index;
    if (start > last) pieces.push({ text: text.slice(last, start), citation: false });
    pieces.push({ text: match[0], citation: true });
    last = start + match[0].length;
  }
  if (last < text.length) pieces.push({ text: text.slice(last), citation: false });
  return pieces;
}
