/**
 * Client-boundary PII scrubbing. Replaces likely identifiers with stable tokens
 * before any payload is assembled. The reverse alias map stays client-side.
 */

const EMAIL_RE = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
const PHONE_RE = /\+?\d[\d\s().-]{7,}\d/g;
const ACCOUNT_RE = /\b\d{8,}\b/g;
// Two consecutive capitalized words: naive person-name heuristic.
const NAME_RE = /\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,20})\b/g;

export interface ScrubResult {
  text: string;
  aliases: Record<string, string>;
}

export function scrubText(input: string, seed: Record<string, string> = {}): ScrubResult {
  const aliases: Record<string, string> = { ...seed };
  const reverse = new Map<string, string>(
    Object.entries(aliases).map(([token, original]) => [original, token]),
  );
  let personCount = 0;
  let acctCount = 0;
  let emailCount = 0;
  let phoneCount = 0;

  const mint = (original: string, prefix: string, next: () => number): string => {
    const existing = reverse.get(original);
    if (existing) return existing;
    const token = `[${prefix}_${next()}]`;
    aliases[token] = original;
    reverse.set(original, token);
    return token;
  };

  let out = input.replace(EMAIL_RE, (m) => mint(m, "EMAIL", () => (emailCount += 1)));
  out = out.replace(ACCOUNT_RE, (m) => mint(m, "ACCT", () => (acctCount += 1)));
  out = out.replace(PHONE_RE, (m) => mint(m, "PHONE", () => (phoneCount += 1)));
  out = out.replace(NAME_RE, (m) => mint(m, "PERSON", () => (personCount += 1)));

  return { text: out, aliases };
}
