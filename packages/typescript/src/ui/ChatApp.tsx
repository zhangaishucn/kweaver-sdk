import React, { useRef, useState } from "react";
import { Box, Static, Text, useApp, useInput } from "ink";
import TextInput from "ink-text-input";
import Spinner from "ink-spinner";

import { type ProgressItem, sendChatRequest, sendChatRequestStream } from "../api/agent-chat.js";

import { formatHttpError } from "../auth/oauth.js";
import { normalizeDisplayText } from "./display-text.js";
import { MarkdownBlock } from "./MarkdownBlock.js";

export interface TokenPayload {
  baseUrl: string;
  accessToken: string;
}

export interface ChatAppProps {
  getToken: () => Promise<TokenPayload>;
  agentId: string;
  agentKey: string;
  agentVersion: string;
  businessDomain: string;
  verbose: boolean;
  initialConversationId?: string;
  stream?: boolean;
}

type MessageRole = "user" | "agent";
type ChatStatus = "idle" | "loading" | "error";

interface Message {
  role: MessageRole;
  content: string;
  /** This agent message was preceded by middle_answer (tool progress). */
  hadProgress?: boolean;
}

const MIDDLE_ANSWER_MAX_LINES = 5;

function formatProgressValue(value: unknown): string {
  if (typeof value === "string") return normalizeDisplayText(value);
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (value === null || value === undefined) return "";
  try {
    return normalizeDisplayText(JSON.stringify(value));
  } catch {
    return String(value);
  }
}

function getLinesForItem(item: ProgressItem, idx: number): string[] {
  const name = item.agent_name ?? item.skill_info?.name ?? `Step ${idx + 1}`;
  const status = item.status ?? "";
  const lines = [`${name}${status ? ` — ${status}` : ""}`];
  const isTool = item.skill_info?.type === "TOOL";

  if (isTool) {
    const toolName = item.skill_info?.name ?? item.agent_name;
    if (toolName) {
      lines.push(`tool: ${normalizeDisplayText(toolName)}`);
    }

    for (const arg of item.skill_info?.args ?? []) {
      const argName = arg.name ?? "arg";
      const argValue = formatProgressValue(arg.value);
      lines.push(`${argName}: ${argValue}`);
    }
  }

  let answerStr: string;
  if (typeof item.answer === "string") {
    answerStr = item.answer;
  } else if (item.answer && typeof item.answer === "object") {
    const o = item.answer as Record<string, unknown>;
    const d = typeof o.description === "string" ? o.description : "";
    const c = typeof o.code === "string" ? o.code : "";
    const s = typeof o.solution === "string" ? o.solution : "";
    const link = typeof o.link === "string" ? o.link : "";
    answerStr = [d, c ? `code: ${c}` : "", s ? `solution: ${s}` : "", link ? `link: ${link}` : ""]
      .filter(Boolean)
      .join("\n");
  } else {
    answerStr = item.result ?? "";
  }
  if (answerStr) lines.push(...normalizeDisplayText(answerStr).split("\n"));
  return lines;
}

interface VisibleProgressItem {
  item: ProgressItem;
  lines: string[];
}

function getVisibleProgress(
  items: ProgressItem[]
): { visible: VisibleProgressItem[]; hiddenLineCount: number } {
  const itemLines = items.map((item, idx) => ({ item, lines: getLinesForItem(item, idx) }));
  let remaining = MIDDLE_ANSWER_MAX_LINES;
  const visible: VisibleProgressItem[] = [];
  for (const { item, lines } of itemLines) {
    if (remaining <= 0) break;
    const take = Math.min(remaining, lines.length);
    visible.push({ item, lines: lines.slice(0, take) });
    remaining -= take;
  }
  const totalLines = itemLines.reduce((s, { lines }) => s + lines.length, 0);
  return { visible, hiddenLineCount: Math.max(0, totalLines - MIDDLE_ANSWER_MAX_LINES) };
}

type StaticItem =
  | { kind: "header" }
  | { kind: "msg"; msg: Message };

function renderStaticItem(item: StaticItem, index: number): React.JSX.Element {
  if (item.kind === "header") {
    return (
      <Box key={index}>
        <Text dimColor>Chat — type exit, quit or q to leave</Text>
      </Box>
    );
  }
  if (item.kind === "msg") {
    const { msg } = item;
    if (msg.role === "user") {
      return (
        <Box key={index} flexDirection="column" marginY={1} width="100%" paddingRight={1}>
          <Box width="100%" paddingX={1} paddingY={1} backgroundColor="#2C2C2C">
            <Text color="#9B9B9B">{normalizeDisplayText(msg.content)}</Text>
          </Box>
        </Box>
      );
    }

    return (
      <Box key={index} flexDirection="column" marginY={1}>
        <>
          {msg.hadProgress ? (
            <Text dimColor>/plan 生成修改计划</Text>
          ) : null}
          <MarkdownBlock content={normalizeDisplayText(msg.content)} />
        </>
      </Box>
    );
  }
  return <Box key={index} />;
}

interface DynamicContentProps {
  toolProgress: ProgressItem[];
  streamingContent: string;
  status: ChatStatus;
  errorMessage: string;
}

const DynamicContent = React.memo(function DynamicContent(
  props: DynamicContentProps
): React.JSX.Element {
  const { toolProgress, streamingContent, status, errorMessage } = props;

  return (
    <Box flexDirection="column">
      {toolProgress.length > 0 ? (
        <Box
          marginY={1}
          borderStyle="single"
          borderColor="gray"
          paddingX={1}
          paddingY={1}
          flexDirection="column"
        >
          <Text bold dimColor>Tool output</Text>
          {(() => {
            const { visible, hiddenLineCount } = getVisibleProgress(toolProgress);
            return (
              <>
                {visible.map(({ item, lines }, i) => {
                  const isTool = item.skill_info?.type === "TOOL";
                  const content = (
                    <>
                      {lines.map((line, j) => (
                        <Text key={j} dimColor>
                          {line}
                        </Text>
                      ))}
                    </>
                  );

                  if (isTool) {
                    return (
                      <Box
                        key={i}
                        marginY={0}
                        borderStyle="single"
                        borderColor="green"
                        paddingX={1}
                        paddingY={0}
                        flexDirection="column"
                      >
                        {content}
                      </Box>
                    );
                  }

                  return (
                    <Box key={i} flexDirection="column">
                      {content}
                    </Box>
                  );
                })}
                {hiddenLineCount > 0 ? (
                  <Text dimColor italic>
                    (已隐藏 {hiddenLineCount} 行)
                  </Text>
                ) : null}
              </>
            );
          })()}
        </Box>
      ) : null}
      {toolProgress.length > 0 && (streamingContent || status === "loading") ? (
        <Text dimColor>/plan 生成修改计划</Text>
      ) : null}
      {streamingContent ? (
        <Box flexDirection="column" marginY={1}>
          <MarkdownBlock content={normalizeDisplayText(streamingContent)} />
        </Box>
      ) : null}
      {errorMessage ? (
        <Box marginY={1}>
          <Text color="red">{errorMessage}</Text>
        </Box>
      ) : null}
    </Box>
  );
});

export function ChatApp(props: ChatAppProps): React.JSX.Element {
  const {
    getToken,
    agentId,
    agentKey,
    agentVersion,
    businessDomain,
    verbose,
    initialConversationId,
    stream: useStream = true,
  } = props;
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [toolProgress, setToolProgress] = useState<ProgressItem[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>(initialConversationId);
  const [inputValue, setInputValue] = useState("");
  const [status, setStatus] = useState<ChatStatus>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const pendingQueriesRef = useRef<string[]>([]);
  const streamingBufferRef = useRef("");
  const toolProgressBufferRef = useRef<ProgressItem[]>([]);
  const streamFlushIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const STREAM_FLUSH_MS = 550;
  const { exit } = useApp();

  const EXIT_WORDS = ["exit", "quit", "q"];

  const doSendQuery = (query: string, convId: string | undefined): void => {
    setMessages((prev: Message[]) => [...prev, { role: "user", content: query }]);
    setInputValue("");
    setStreamingContent("");
    setToolProgress([]);
    setErrorMessage("");
    setStatus("loading");
    streamingBufferRef.current = "";
    toolProgressBufferRef.current = [];

    const onDone = (result: {
      text: string;
      conversationId?: string;
      progress?: ProgressItem[];
    }): void => {
      const hadProgress =
        (result.progress?.length ?? 0) > 0 || toolProgressBufferRef.current.length > 0;
      setStreamingContent("");
      setToolProgress(
        result.progress !== undefined ? result.progress : toolProgressBufferRef.current
      );
      setMessages((prev: Message[]) => [
        ...prev,
        { role: "agent", content: normalizeDisplayText(result.text), hadProgress },
      ]);
      if (result.conversationId) {
        setConversationId(result.conversationId);
      }
      setStatus("idle");
      const next = pendingQueriesRef.current.shift();
      if (next !== undefined) {
        doSendQuery(next, result.conversationId);
      }
    };

    const onFail = (error: unknown): void => {
      setErrorMessage(formatHttpError(error));
      setStatus("error");
      setStreamingContent("");
      setToolProgress([]);
      const next = pendingQueriesRef.current.shift();
      if (next !== undefined) {
        pendingQueriesRef.current.unshift(next);
      }
    };

    if (!useStream) {
      void getToken()
        .then((token) =>
          sendChatRequest({
            baseUrl: token.baseUrl,
            accessToken: token.accessToken,
            agentId,
            agentKey,
            agentVersion,
            query,
            conversationId: convId,
            stream: false,
            verbose,
            businessDomain,
          })
        )
        .then(onDone)
        .catch(onFail);
      return;
    }

    if (streamFlushIntervalRef.current) {
      clearInterval(streamFlushIntervalRef.current);
      streamFlushIntervalRef.current = null;
    }
    streamFlushIntervalRef.current = setInterval(() => {
      const nextText = streamingBufferRef.current;
      const nextProgress = toolProgressBufferRef.current;
      const normalizedNextText = normalizeDisplayText(nextText);
      setStreamingContent((prev) => (normalizedNextText === prev ? prev : normalizedNextText));
      setToolProgress((prev) =>
        prev.length !== nextProgress.length || prev.some((p, i) => p !== nextProgress[i])
          ? nextProgress
          : prev
      );
    }, STREAM_FLUSH_MS);

    void getToken()
      .then((token) =>
        sendChatRequestStream(
          {
            baseUrl: token.baseUrl,
            accessToken: token.accessToken,
            agentId,
            agentKey,
            agentVersion,
            query,
            conversationId: convId,
            stream: true,
            verbose,
            businessDomain,
          },
          {
            onTextDelta: (fullText) => {
              streamingBufferRef.current = normalizeDisplayText(fullText);
            },
            onProgress: (progress) => {
              toolProgressBufferRef.current = progress;
            },
          }
        )
      )
      .then((result) => {
        if (streamFlushIntervalRef.current) {
          clearInterval(streamFlushIntervalRef.current);
          streamFlushIntervalRef.current = null;
        }
        streamingBufferRef.current = "";
        onDone(result);
      })
      .catch((error: unknown) => {
        if (streamFlushIntervalRef.current) {
          clearInterval(streamFlushIntervalRef.current);
          streamFlushIntervalRef.current = null;
        }
        streamingBufferRef.current = "";
        onFail(error);
      });
  };

  useInput((input, key) => {
    if (key.ctrl && input === "\x03") {
      exit();
    }
  });

  const handleSubmit = (value: string): void => {
    const trimmed = value.trim();
    if (!trimmed) return;

    if (EXIT_WORDS.includes(trimmed.toLowerCase())) {
      exit();
      return;
    }

    if (status === "loading") {
      pendingQueriesRef.current.push(trimmed);
      setInputValue("");
      return;
    }

    doSendQuery(trimmed, conversationId);
  };

  const staticItems: StaticItem[] = [
    { kind: "header" },
    ...messages.map((msg) => ({ kind: "msg" as const, msg })),
  ];

  return (
    <Box flexDirection="column" padding={1}>
      <Static items={staticItems} style={{ width: "100%" }}>
        {(item, index) => renderStaticItem(item, index)}
      </Static>
      <DynamicContent
        toolProgress={toolProgress}
        streamingContent={streamingContent}
        status={status}
        errorMessage={errorMessage}
      />
      <Box
        marginTop={1}
        borderStyle="single"
        borderColor="gray"
        backgroundColor="black"
        paddingX={1}
        paddingY={0}
      >
        <Text color="gray">{"> "}</Text>
        <TextInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          placeholder="Type a message..."
        />
      </Box>
      {status === "loading" ? (
        <Box marginTop={1}>
          <Text color="green">
            <Spinner type="dots" />
          </Text>
          <Text> Thinking...</Text>
        </Box>
      ) : null}
    </Box>
  );
}
