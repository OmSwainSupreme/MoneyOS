import { useEffect, useRef, useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { DefaultChatTransport } from "ai";
import { useChat } from "@ai-sdk/react";
import ReactMarkdown from "react-markdown";
import { create } from "zustand";
//#region src/services/ai/pii.ts
/**
* Client-boundary PII scrubbing. Replaces likely identifiers with stable tokens
* before any payload is assembled. The reverse alias map stays client-side.
*/
var EMAIL_RE = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
var PHONE_RE = /\+?\d[\d\s().-]{7,}\d/g;
var ACCOUNT_RE = /\b\d{8,}\b/g;
var NAME_RE = /\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,20})\b/g;
function scrubText(input, seed = {}) {
	const aliases = { ...seed };
	const reverse = new Map(Object.entries(aliases).map(([token, original]) => [original, token]));
	let personCount = 0;
	let acctCount = 0;
	let emailCount = 0;
	let phoneCount = 0;
	const mint = (original, prefix, next) => {
		const existing = reverse.get(original);
		if (existing) return existing;
		const token = `[${prefix}_${next()}]`;
		aliases[token] = original;
		reverse.set(original, token);
		return token;
	};
	let out = input.replace(EMAIL_RE, (m) => mint(m, "EMAIL", () => emailCount += 1));
	out = out.replace(ACCOUNT_RE, (m) => mint(m, "ACCT", () => acctCount += 1));
	out = out.replace(PHONE_RE, (m) => mint(m, "PHONE", () => phoneCount += 1));
	out = out.replace(NAME_RE, (m) => mint(m, "PERSON", () => personCount += 1));
	return {
		text: out,
		aliases
	};
}
//#endregion
//#region src/lib/store/aiStore.ts
var useAIStore = create((set) => ({
	messages: [],
	status: "idle",
	contextSummary: "",
	piiMap: {},
	errorMessage: null,
	appendMessage: (m) => set((s) => ({ messages: [...s.messages, m].slice(-200) })),
	setStatus: (status) => set({ status }),
	setError: (errorMessage) => set({ errorMessage }),
	setContextSummary: (contextSummary) => set({ contextSummary }),
	mergePii: (aliases) => set((s) => ({ piiMap: {
		...s.piiMap,
		...aliases
	} })),
	clearChat: () => set({
		messages: [],
		status: "idle",
		contextSummary: "",
		piiMap: {},
		errorMessage: null
	})
}));
//#endregion
//#region src/routes/chat.tsx?tsr-split=component
function ChatPage() {
	const { messages, sendMessage, status, error } = useChat({ transport: useRef(new DefaultChatTransport({ api: "/api/chat" })).current });
	const mergePii = useAIStore((s) => s.mergePii);
	const [input, setInput] = useState("");
	const textareaRef = useRef(null);
	const bottomRef = useRef(null);
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
	const handleSubmit = (e) => {
		e.preventDefault();
		const trimmed = input.trim();
		if (!trimmed || busy) return;
		const { text, aliases } = scrubText(trimmed);
		if (Object.keys(aliases).length > 0) mergePii(aliases);
		sendMessage({ text });
		setInput("");
	};
	return /* @__PURE__ */ jsxs("div", {
		className: "mx-auto flex h-[calc(100vh-4rem)] max-w-3xl flex-col px-4 py-6 sm:px-6 md:h-screen",
		children: [
			/* @__PURE__ */ jsxs("header", {
				className: "mb-4",
				children: [/* @__PURE__ */ jsx("h1", {
					className: "text-2xl font-semibold tracking-tight text-foreground",
					children: "Assistant"
				}), /* @__PURE__ */ jsx("p", {
					className: "text-sm text-muted-foreground",
					children: "PII is scrubbed at the client boundary before any request leaves this tab."
				})]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "flex-1 overflow-y-auto rounded-md border border-border bg-card p-4",
				"aria-live": "polite",
				"aria-atomic": "false",
				children: [
					messages.length === 0 ? /* @__PURE__ */ jsx("p", {
						className: "text-sm text-muted-foreground",
						children: "Ask a question about your cash flow, budgets, or an upcoming decision."
					}) : /* @__PURE__ */ jsx("ul", {
						className: "space-y-4",
						children: messages.map((m) => /* @__PURE__ */ jsx(MessageRow, { message: m }, m.id))
					}),
					status === "submitted" ? /* @__PURE__ */ jsxs("div", {
						className: "mt-3 flex items-center gap-2 text-sm text-muted-foreground",
						children: [/* @__PURE__ */ jsx("span", { className: "inline-block h-2 w-2 animate-pulse rounded-full bg-muted-foreground" }), "Thinking…"]
					}) : null,
					error ? /* @__PURE__ */ jsx("p", {
						role: "alert",
						className: "mt-3 text-sm text-[color:var(--color-danger-zone)]",
						children: error.message
					}) : null,
					/* @__PURE__ */ jsx("div", { ref: bottomRef })
				]
			}),
			/* @__PURE__ */ jsxs("form", {
				onSubmit: handleSubmit,
				className: "mt-4 flex items-end gap-2",
				children: [
					/* @__PURE__ */ jsx("label", {
						htmlFor: "chat-input",
						className: "sr-only",
						children: "Message"
					}),
					/* @__PURE__ */ jsx("textarea", {
						id: "chat-input",
						ref: textareaRef,
						value: input,
						onChange: (e) => setInput(e.target.value),
						onKeyDown: (e) => {
							if (e.key === "Enter" && !e.shiftKey) {
								e.preventDefault();
								handleSubmit(e);
							}
						},
						rows: 2,
						placeholder: "Ask MoneyOS…",
						className: "min-h-11 flex-1 resize-none rounded-md border border-input bg-background p-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
					}),
					/* @__PURE__ */ jsx("button", {
						type: "submit",
						disabled: busy || input.trim().length === 0,
						className: "inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50",
						children: "Send"
					})
				]
			})
		]
	});
}
function MessageRow({ message }) {
	const isUser = message.role === "user";
	const text = message.parts.filter((p) => p.type === "text").map((p) => p.text).join("");
	return /* @__PURE__ */ jsx("li", {
		className: isUser ? "flex justify-end" : "flex justify-start",
		children: /* @__PURE__ */ jsx("div", {
			className: `max-w-[85%] rounded-md px-3 py-2 text-sm ${isUser ? "bg-primary text-primary-foreground" : "border border-border bg-background text-foreground"}`,
			children: isUser ? /* @__PURE__ */ jsx("p", {
				className: "whitespace-pre-wrap",
				children: text
			}) : /* @__PURE__ */ jsx("div", {
				className: "prose prose-sm max-w-none dark:prose-invert",
				children: /* @__PURE__ */ jsx(ReactMarkdown, { children: text })
			})
		})
	});
}
//#endregion
export { ChatPage as component };
