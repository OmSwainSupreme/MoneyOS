import { createFileRoute } from "@tanstack/react-router";
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

// Backend chat endpoint (FastAPI, /api/v1/ai/chat). The frontend talks to
// it via the Vite dev proxy (relative /api paths) so the browser stays
// same-origin and avoids cross-origin CORS blocks. A demo user is minted
// once per tab so the endpoint's auth requirement is satisfied.
const CHAT_API = "/api/v1/ai/chat";
const REGISTER_API = "/api/v1/auth/register";
const LOGIN_API = "/api/v1/auth/login";

const DEMO_EMAIL = "demo@moneyos.dev";
const DEMO_PASSWORD = "Demo!pass1";
const DEMO_NAME = "Demo User";

type Role = "user" | "assistant";
interface ChatLine {
  id: string;
  role: Role;
  text: string;
}

let tokenCache: string | null = null;

async function getToken(): Promise<string> {
  if (tokenCache) return tokenCache;
  // Register is idempotent-ish; if the user already exists, fall back to login.
  const register = await fetch(REGISTER_API, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      email: DEMO_EMAIL,
      password: DEMO_PASSWORD,
      full_name: DEMO_NAME,
    }),
  });
  let token: string | null = null;
  if (register.ok) {
    // Registered but not auto-logged-in; exchange credentials for a token.
    token = await loginAndGetToken();
  } else {
    token = await loginAndGetToken();
  }
  if (!token) throw new Error("Could not authenticate with the assistant.");
  tokenCache = token;
  return token;
}

async function loginAndGetToken(): Promise<string | null> {
  const res = await fetch(LOGIN_API, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access_token?: string };
  return data.access_token ?? null;
}

function ChatPage() {
  const mergePii = useAIStore((s) => s.mergePii);
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!busy) textareaRef.current?.focus();
  }, [busy]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines, busy]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || busy) return;

    // Scrub PII at the client boundary before anything leaves the tab.
    const { text, aliases } = scrubText(trimmed);
    if (Object.keys(aliases).length > 0) mergePii(aliases);

    const userLine: ChatLine = {
      id: `u-${Date.now()}`,
      role: "user",
      text: trimmed,
    };
    const history = [...lines, userLine].map((l) => ({
      role: l.role,
      content: l.text,
    }));

    setLines((prev) => [...prev, userLine]);
    setInput("");
    setBusy(true);
    setError(null);

    try {
      const token = await getToken();
      const res = await fetch(CHAT_API, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: text, history }),
      });
      if (!res.ok) {
        const detail = await res.text().catch(() => "");
        throw new Error(`Assistant error (${res.status}). ${detail}`.trim());
      }
      const data = (await res.json()) as { reply?: string };
      setLines((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: data.reply ?? "_(no reply)_",
        },
      ]);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "The assistant is unavailable.",
      );
    } finally {
      setBusy(false);
    }
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
        {lines.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Ask a question about your cash flow, budgets, or an upcoming decision.
          </p>
        ) : (
          <ul className="space-y-4">
            {lines.map((m) => (
              <MessageRow key={m.id} line={m} />
            ))}
          </ul>
        )}
        {busy ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
            Thinking…
          </div>
        ) : null}
        {error ? (
          <p role="alert" className="mt-3 text-sm text-[color:var(--color-danger-zone)]">
            {error}
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

function MessageRow({ line }: { line: ChatLine }) {
  const isUser = line.role === "user";
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
          <p className="whitespace-pre-wrap">{line.text}</p>
        ) : (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{line.text}</ReactMarkdown>
          </div>
        )}
      </div>
    </li>
  );
}
