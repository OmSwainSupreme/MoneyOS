import { Link } from "@tanstack/react-router";
import { jsx, jsxs } from "react/jsx-runtime";
//#region src/routes/index.tsx?tsr-split=component
function Landing() {
	return /* @__PURE__ */ jsxs("div", {
		className: "mx-auto max-w-3xl px-6 py-16",
		children: [
			/* @__PURE__ */ jsx("h1", {
				className: "text-3xl font-semibold tracking-tight text-foreground sm:text-4xl",
				children: "Clear financial decisions, backed by your own numbers."
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-4 text-base text-muted-foreground",
				children: "MoneyOS ingests your cash flow and liabilities, tracks overspending in real time, and stress-tests purchases and loans before you commit. Nothing leaves your browser unless you explicitly ask the assistant."
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "mt-8 flex flex-wrap gap-3",
				children: [/* @__PURE__ */ jsx(Link, {
					to: "/dashboard",
					className: "inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90",
					children: "Open dashboard"
				}), /* @__PURE__ */ jsx(Link, {
					to: "/import",
					className: "inline-flex min-h-11 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground hover:bg-accent",
					children: "Import a statement"
				})]
			}),
			/* @__PURE__ */ jsxs("section", {
				className: "mt-12 grid gap-4 sm:grid-cols-2",
				children: [
					/* @__PURE__ */ jsx(FeatureCard, {
						title: "High-trust dashboard",
						body: "Net cash flow, savings rate, overspend alarms, and asset/liability ratio at a glance."
					}),
					/* @__PURE__ */ jsx(FeatureCard, {
						title: "Sandboxed import",
						body: "CSV or JSON parsed entirely in-browser with row-level validation before anything is stored."
					}),
					/* @__PURE__ */ jsx(FeatureCard, {
						title: "Decision wizards",
						body: "Structured \"Can I buy this?\" and \"Should I take this loan?\" flows with typed inputs."
					}),
					/* @__PURE__ */ jsx(FeatureCard, {
						title: "Bounded AI",
						body: "Chat context is scrubbed of names, emails, phone and account numbers at the client boundary."
					})
				]
			})
		]
	});
}
function FeatureCard({ title, body }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "rounded-md border border-border bg-card p-4",
		children: [/* @__PURE__ */ jsx("h2", {
			className: "text-sm font-semibold text-card-foreground",
			children: title
		}), /* @__PURE__ */ jsx("p", {
			className: "mt-1 text-sm text-muted-foreground",
			children: body
		})]
	});
}
//#endregion
export { Landing as component };
