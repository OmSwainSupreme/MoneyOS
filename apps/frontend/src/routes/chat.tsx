import { createFileRoute } from "@tanstack/react-router";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type UIMessage } from "ai";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { scrubText } from "@/services/ai/pii";
import { useAIStore } from "@/lib/store/aiStore";

export const Route = createFileRoute("/chat")({
  head: () => ({
    meta: [
      { title: "Assistant · MoneyOS" },
      {
        name: "description",
        content:
          "Ask financial questions. Names, emails, phone and account numbers are scrubbed before requests leave your browser.",
      },
      { property: "og:title", content: "Assistant · MoneyOS" },
      {
        property: "og:description",
        content: "PII-scrubbed AI assistant for financial questions.",
      },
    ],
  }),
  component: ChatPage,
});

function ChatPage() {
  const transportRef = useRef(new DefaultChatTransport({ api: "/api/chat" }));
  const { messages, sendMessage, status, error } = useChat({
    transport: transportRef.current,
  });
  const mergePii = useAIStore((s) => s.mergePii);
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const busy = status === "submitted" || status === "streaming";

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!busy) textareaRef.current?.focus();
  }, [busy]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || busy) return;
    const { text, aliases } = scrubText(trimmed);
    if (Object.keys(aliases).length > 0) mergePii(aliases);
    void sendMessage({ text });
    setInput("");
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-3xl flex-col px-4 py-6 sm:px-6 md:h-screen">
      <header className="mb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Assistant
        </h1>
        <p className="text-sm text-muted-foreground">
          PII is scrubbed at the client boundary before any request leaves this tab.
        </p>
      </header>
      <div
        className="flex-1 overflow-y-auto rounded-md border border-border bg-card p-4"
        aria-live="polite"
        aria-atomic="false"
      >
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Ask a question about your cash flow, budgets, or an upcoming decision.
          </p>
        ) : (
          <ul className="space-y-4">
            {messages.map((m: UIMessage) => (
              <MessageRow key={m.id} message={m} />
            ))}
          </ul>
        )}
        {status === "submitted" ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
            Thinking…
          </div>
        ) : null}
        {error ? (
          <p role="alert" className="mt-3 text-sm text-[color:var(--color-danger-zone)]">
            {error.message}
          </p>
        ) : null}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="mt-4 flex items-end gap-2">
        <label htmlFor="chat-input" className="sr-only">
          Message
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          rows={2}
          placeholder="Ask MoneyOS…"
          className="min-h-11 flex-1 resize-none rounded-md border border-input bg-background p-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <button
          type="submit"
          disabled={busy || input.trim().length === 0}
          className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function MessageRow({ message }: { message: UIMessage }) {
  const isUser = message.role === "user";
  const text = message.parts
    .filter((p): p is Extract<UIMessage["parts"][number], { type: "text" }> => p.type === "text")
    .map((p) => p.text)
    .join("");
  return (
    <li className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={`max-w-[85%] rounded-md px-3 py-2 text-sm ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "border border-border bg-background text-foreground"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{text}</p>
        ) : (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
        )}
      </div>
    </li>
  );
}
