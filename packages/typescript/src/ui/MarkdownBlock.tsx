import React, { Fragment, useMemo } from "react";
import { Box, Text } from "ink";
import { marked, type Token, type Tokens } from "marked";
import { normalizeDisplayText } from "./display-text.js";

function hasTokens(token: Token): token is Token & { tokens: Token[] } {
  return "tokens" in token && Array.isArray(token.tokens);
}

function isListToken(token: Token): token is Tokens.List {
  return token.type === "list" && "items" in token;
}

function isTableToken(token: Token): token is Tokens.Table {
  return token.type === "table" && "header" in token && "rows" in token;
}

function tokensToPlainText(tokens: Token[] | undefined): string {
  if (!tokens || tokens.length === 0) return "";

  return tokens
    .map((token) => {
      switch (token.type) {
        case "text":
          return hasTokens(token) ? tokensToPlainText(token.tokens) : token.text;
        case "strong":
        case "em":
        case "del":
          return tokensToPlainText(token.tokens ?? []);
        case "codespan":
          return `\`${token.text}\``;
        case "link":
          return `${tokensToPlainText(token.tokens ?? [])} (${token.href})`;
        case "image":
          return `[image: ${token.text || token.href}]`;
        case "br":
          return "\n";
        case "escape":
        case "html":
          return token.text;
        default:
          if (hasTokens(token)) {
            return tokensToPlainText(token.tokens);
          }
          if ("text" in token && typeof token.text === "string") {
            return token.text;
          }
          return token.raw;
      }
    })
    .join("");
}

function renderInlineToken(token: Token, key: string): React.ReactNode {
  switch (token.type) {
    case "text":
      if (hasTokens(token)) {
        return <Fragment key={key}>{renderInlineTokens(token.tokens, `${key}-text`)}</Fragment>;
      }
      return <Fragment key={key}>{token.text}</Fragment>;
    case "strong":
      return (
        <Text key={key} bold>
          {renderInlineTokens(token.tokens ?? [], `${key}-strong`)}
        </Text>
      );
    case "em":
      return (
        <Text key={key} italic>
          {renderInlineTokens(token.tokens ?? [], `${key}-em`)}
        </Text>
      );
    case "del":
      return (
        <Text key={key} dimColor>
          {renderInlineTokens(token.tokens ?? [], `${key}-del`)}
        </Text>
      );
    case "codespan":
      return (
        <Text key={key} color="cyan">
          {` \`${token.text}\` `}
        </Text>
      );
    case "link":
      return (
        <Text key={key} color="blue" underline>
          {renderInlineTokens(token.tokens ?? [], `${key}-link`)}
          {` (${token.href})`}
        </Text>
      );
    case "image":
      return (
        <Text key={key} color="yellow">
          [{token.text || "image"}] {token.href}
        </Text>
      );
    case "br":
      return <Fragment key={key}>{"\n"}</Fragment>;
    case "escape":
    case "html":
      return <Fragment key={key}>{token.text}</Fragment>;
    default:
      if (hasTokens(token)) {
        return <Fragment key={key}>{renderInlineTokens(token.tokens, `${key}-generic`)}</Fragment>;
      }
      if ("text" in token && typeof token.text === "string") {
        return <Fragment key={key}>{token.text}</Fragment>;
      }
      return <Fragment key={key}>{token.raw}</Fragment>;
  }
}

function renderInlineTokens(tokens: Token[], keyPrefix: string): React.ReactNode[] {
  return tokens.map((token, index) => renderInlineToken(token, `${keyPrefix}-${index}`));
}

function renderTable(token: Tokens.Table, key: string): React.JSX.Element {
  const rows = [
    token.header.map((cell) => tokensToPlainText(cell.tokens)),
    ...token.rows.map((row) => row.map((cell) => tokensToPlainText(cell.tokens))),
  ];

  return (
    <Box key={key} flexDirection="column" marginBottom={1} borderStyle="single" borderColor="gray" paddingX={1}>
      {rows.map((row, rowIndex) => (
        <Text key={`${key}-row-${rowIndex}`}>
          {row.join(" | ")}
        </Text>
      ))}
    </Box>
  );
}

function renderList(token: Tokens.List, key: string): React.JSX.Element {
  const start = typeof token.start === "number" ? token.start : 1;

  return (
    <Box key={key} flexDirection="column" marginBottom={1}>
      {token.items.map((item, index) => {
        const marker = token.ordered ? `${start + index}.` : "•";
        const text = tokensToPlainText(item.tokens).trim();
        return (
          <Box key={`${key}-item-${index}`}>
            <Text>{`${marker} ${text}`}</Text>
          </Box>
        );
      })}
    </Box>
  );
}

function renderBlock(token: Token, key: string): React.JSX.Element | null {
  switch (token.type) {
    case "space":
      return null;
    case "heading":
      return (
        <Box key={key} marginBottom={1}>
          <Text bold color={token.depth <= 2 ? "cyan" : "green"}>
            {renderInlineTokens(token.tokens ?? [], `${key}-heading`)}
          </Text>
        </Box>
      );
    case "paragraph":
      return (
        <Box key={key} marginBottom={1}>
          <Text>{renderInlineTokens(token.tokens ?? [], `${key}-paragraph`)}</Text>
        </Box>
      );
    case "text":
      return (
        <Box key={key} marginBottom={1}>
          <Text>{hasTokens(token) ? renderInlineTokens(token.tokens, `${key}-text`) : token.text}</Text>
        </Box>
      );
    case "code":
      return (
        <Box
          key={key}
          flexDirection="column"
          marginBottom={1}
          borderStyle="single"
          borderColor="gray"
          paddingX={1}
        >
          {token.lang ? <Text dimColor>{token.lang}</Text> : null}
          {token.text.split("\n").map((line: string, index: number) => (
            <Text key={`${key}-line-${index}`} color="cyan">
              {line}
            </Text>
          ))}
        </Box>
      );
    case "blockquote": {
      const lines = tokensToPlainText(token.tokens).split("\n");
      return (
        <Box key={key} flexDirection="column" marginBottom={1} paddingLeft={1}>
          {lines.map((line, index) => (
            <Text key={`${key}-quote-${index}`} dimColor>
              {`> ${line}`}
            </Text>
          ))}
        </Box>
      );
    }
    case "list":
      return isListToken(token) ? renderList(token, key) : null;
    case "table":
      return isTableToken(token) ? renderTable(token, key) : null;
    case "hr":
      return (
        <Box key={key} marginBottom={1}>
          <Text dimColor>----------------------------------------</Text>
        </Box>
      );
    case "html":
      return token.block ? (
        <Box key={key} marginBottom={1}>
          <Text>{token.text}</Text>
        </Box>
      ) : null;
    default:
      return (
        <Box key={key} marginBottom={1}>
          <Text>{tokensToPlainText(hasTokens(token) ? token.tokens : undefined) || token.raw}</Text>
        </Box>
      );
  }
}

export interface MarkdownBlockProps {
  content: string;
}

export function MarkdownBlock({ content }: MarkdownBlockProps): React.JSX.Element {
  const trimmed = normalizeDisplayText(content).trim();
  const tokens = useMemo(() => (trimmed ? marked.lexer(trimmed) : []), [trimmed]);

  if (!trimmed) {
    return <Text />;
  }

  return <Box flexDirection="column">{tokens.map((token, index) => renderBlock(token, `md-${index}`))}</Box>;
}
