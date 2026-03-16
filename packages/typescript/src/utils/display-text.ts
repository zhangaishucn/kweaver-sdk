function decodeHtmlEntitiesPass(s: string): string {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([0-9a-fA-F]+);/g, (_, code) => String.fromCodePoint(parseInt(code, 16)))
    .replace(/&quot;/g, "\"")
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&nbsp;/g, " ");
}

export function decodeHtmlEntities(s: string): string {
  let current = s;

  for (let i = 0; i < 5; i += 1) {
    const decoded = decodeHtmlEntitiesPass(current);
    if (decoded === current) {
      break;
    }
    current = decoded;
  }

  return current;
}

export function stripHtmlComments(s: string): string {
  let current = s.trimStart();

  // Suppress leading comment-only frames during streaming, but keep text that follows
  // once the leading comment block is complete.
  while (current.startsWith("<!--")) {
    const endIdx = current.indexOf("-->");
    if (endIdx === -1) {
      return "";
    }
    current = current.slice(endIdx + 3).trimStart();
  }

  return current.replace(/<!--[\s\S]*?-->/g, "").trim();
}

export function normalizeDisplayText(s: string): string {
  let current = s;

  for (let i = 0; i < 5; i += 1) {
    const normalized = stripHtmlComments(decodeHtmlEntities(current));
    if (normalized === current) {
      break;
    }
    current = normalized;
  }

  return current;
}
