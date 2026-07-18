import { useEffect } from "react";
import { HeadContent, Link, Outlet, Scripts, createFileRoute, createRootRouteWithContext, createRouter, lazyRouteComponent, useRouter } from "@tanstack/react-router";
import { jsx, jsxs } from "react/jsx-runtime";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
//#region src/styles.css?url
var styles_default = "/assets/styles-27DSNTv3.css";
//#endregion
//#region src/lib/lovable-error-reporting.ts
function reportLovableError(error, context = {}) {
	if (typeof window === "undefined") return;
	window.__lovableEvents?.captureException?.(error, {
		source: "react_error_boundary",
		route: window.location.pathname,
		...context
	}, {
		mechanism: "react_error_boundary",
		handled: false,
		severity: "error"
	});
	const message = error instanceof Response ? `Response ${error.status}${error.url ? ` at ${error.url}` : ""}` : error instanceof Error ? error.message : String(error);
	window.__lovableReportRuntimeError?.({
		message,
		stack: error instanceof Error ? error.stack : void 0,
		filename: window.location.pathname
	});
}
//#endregion
//#region src/routes/__root.tsx
function NotFoundComponent() {
	return /* @__PURE__ */ jsx("div", {
		className: "flex min-h-screen items-center justify-center bg-background px-4",
		children: /* @__PURE__ */ jsxs("div", {
			className: "max-w-md text-center",
			children: [
				/* @__PURE__ */ jsx("h1", {
					className: "text-7xl font-bold text-foreground",
					children: "404"
				}),
				/* @__PURE__ */ jsx("h2", {
					className: "mt-4 text-xl font-semibold text-foreground",
					children: "Page not found"
				}),
				/* @__PURE__ */ jsx("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: "The page you're looking for doesn't exist or has been moved."
				}),
				/* @__PURE__ */ jsx("div", {
					className: "mt-6",
					children: /* @__PURE__ */ jsx(Link, {
						to: "/",
						className: "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
						children: "Go home"
					})
				})
			]
		})
	});
}
function ErrorComponent({ error, reset }) {
	console.error(error);
	const router = useRouter();
	useEffect(() => {
		reportLovableError(error, { boundary: "tanstack_root_error_component" });
	}, [error]);
	return /* @__PURE__ */ jsx("div", {
		className: "flex min-h-screen items-center justify-center bg-background px-4",
		children: /* @__PURE__ */ jsxs("div", {
			className: "max-w-md text-center",
			children: [
				/* @__PURE__ */ jsx("h1", {
					className: "text-xl font-semibold tracking-tight text-foreground",
					children: "This page didn't load"
				}),
				/* @__PURE__ */ jsx("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: "Something went wrong on our end. You can try refreshing or head back home."
				}),
				/* @__PURE__ */ jsxs("div", {
					className: "mt-6 flex flex-wrap justify-center gap-2",
					children: [/* @__PURE__ */ jsx("button", {
						onClick: () => {
							router.invalidate();
							reset();
						},
						className: "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
						children: "Try again"
					}), /* @__PURE__ */ jsx("a", {
						href: "/",
						className: "inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent",
						children: "Go home"
					})]
				})
			]
		})
	});
}
var Route$7 = createRootRouteWithContext()({
	head: () => ({
		meta: [
			{ charSet: "utf-8" },
			{
				name: "viewport",
				content: "width=device-width, initial-scale=1"
			},
			{ title: "MoneyOS — AI Financial Decision Engine" },
			{
				name: "description",
				content: "MoneyOS turns your cash flow, budgets and liabilities into clear, AI-assisted financial decisions."
			},
			{
				name: "author",
				content: "MoneyOS"
			},
			{
				property: "og:title",
				content: "MoneyOS — AI Financial Decision Engine"
			},
			{
				property: "og:description",
				content: "Track cash flow, spot overspending, and stress-test purchases and loans before you commit."
			},
			{
				property: "og:type",
				content: "website"
			},
			{
				name: "twitter:card",
				content: "summary_large_image"
			}
		],
		links: [{
			rel: "stylesheet",
			href: styles_default
		}, {
			rel: "icon",
			href: "/favicon.ico",
			type: "image/x-icon"
		}]
	}),
	shellComponent: RootShell,
	component: RootComponent,
	notFoundComponent: NotFoundComponent,
	errorComponent: ErrorComponent
});
function RootShell({ children }) {
	return /* @__PURE__ */ jsxs("html", {
		lang: "en",
		children: [/* @__PURE__ */ jsx("head", { children: /* @__PURE__ */ jsx(HeadContent, {}) }), /* @__PURE__ */ jsxs("body", { children: [children, /* @__PURE__ */ jsx(Scripts, {})] })]
	});
}
var NAV = [
	{
		to: "/",
		label: "Home"
	},
	{
		to: "/dashboard",
		label: "Dashboard"
	},
	{
		to: "/import",
		label: "Import"
	},
	{
		to: "/chat",
		label: "Chat"
	},
	{
		to: "/decide/purchase",
		label: "Purchase"
	},
	{
		to: "/decide/loan",
		label: "Loan"
	}
];
function RootComponent() {
	const { queryClient } = Route$7.useRouteContext();
	return /* @__PURE__ */ jsxs(QueryClientProvider, {
		client: queryClient,
		children: [/* @__PURE__ */ jsx("a", {
			href: "#main",
			className: "sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground",
			children: "Skip to content"
		}), /* @__PURE__ */ jsxs("div", {
			className: "flex min-h-screen flex-col md:flex-row",
			children: [/* @__PURE__ */ jsxs("nav", {
				"aria-label": "Primary",
				className: "border-b border-border bg-sidebar text-sidebar-foreground md:min-h-screen md:w-56 md:border-b-0 md:border-r",
				children: [/* @__PURE__ */ jsx("div", {
					className: "flex items-center justify-between px-4 py-4 md:block",
					children: /* @__PURE__ */ jsx(Link, {
						to: "/",
						className: "text-sm font-semibold tracking-tight",
						children: "MoneyOS"
					})
				}), /* @__PURE__ */ jsx("ul", {
					className: "flex gap-1 overflow-x-auto px-2 pb-2 md:mt-2 md:flex-col md:gap-0.5 md:overflow-visible md:px-2",
					children: NAV.map((item) => /* @__PURE__ */ jsx("li", { children: /* @__PURE__ */ jsx(Link, {
						to: item.to,
						className: "block rounded-md px-3 py-2 text-sm text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
						activeProps: { className: "block rounded-md px-3 py-2 text-sm bg-sidebar-accent text-sidebar-accent-foreground font-medium" },
						activeOptions: { exact: item.to === "/" },
						children: item.label
					}) }, item.to))
				})]
			}), /* @__PURE__ */ jsx("main", {
				id: "main",
				className: "flex-1 bg-background text-foreground",
				children: /* @__PURE__ */ jsx(Outlet, {})
			})]
		})]
	});
}
//#endregion
//#region src/routes/index.tsx
var $$splitComponentImporter$6 = () => import("./routes-4ZYSgo-l.js");
var Route$6 = createFileRoute("/")({ component: lazyRouteComponent($$splitComponentImporter$6, "component") });
//#endregion
//#region src/routes/chat.tsx
var $$splitComponentImporter$5 = () => import("./chat-vH56OXTG.js");
var Route$5 = createFileRoute("/chat")({
	head: () => ({ meta: [
		{ title: "Assistant · MoneyOS" },
		{
			name: "description",
			content: "Ask financial questions. Names, emails, phone and account numbers are scrubbed before requests leave your browser."
		},
		{
			property: "og:title",
			content: "Assistant · MoneyOS"
		},
		{
			property: "og:description",
			content: "PII-scrubbed AI assistant for financial questions."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$5, "component")
});
//#endregion
//#region src/routes/dashboard.tsx
var $$splitComponentImporter$4 = () => import("./dashboard-CzZ83OIG.js");
var Route$4 = createFileRoute("/dashboard")({
	head: () => ({ meta: [
		{ title: "Dashboard · MoneyOS" },
		{
			name: "description",
			content: "Cash flow, savings rate, overspend alarms, and asset/liability ratio in one view."
		},
		{
			property: "og:title",
			content: "Dashboard · MoneyOS"
		},
		{
			property: "og:description",
			content: "High-trust overview of your monthly finances."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$4, "component")
});
//#endregion
//#region src/routes/decide.tsx
var $$splitComponentImporter$3 = () => import("./decide-OegJBprO.js");
var Route$3 = createFileRoute("/decide")({ component: lazyRouteComponent($$splitComponentImporter$3, "component") });
//#endregion
//#region src/routes/import.tsx
var $$splitComponentImporter$2 = () => import("./import-DUua_FF7.js");
var Route$2 = createFileRoute("/import")({
	head: () => ({ meta: [
		{ title: "Import statement · MoneyOS" },
		{
			name: "description",
			content: "Sandboxed in-browser CSV or JSON parsing with row-level validation."
		},
		{
			property: "og:title",
			content: "Import statement · MoneyOS"
		},
		{
			property: "og:description",
			content: "Parse and validate your statements before anything is stored."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$2, "component")
});
//#endregion
//#region src/routes/decide.loan.tsx
var $$splitComponentImporter$1 = () => import("./decide.loan-BKhIdniH.js");
var Route$1 = createFileRoute("/decide/loan")({
	head: () => ({ meta: [
		{ title: "Should I take this loan? · MoneyOS" },
		{
			name: "description",
			content: "Estimate monthly payment, total interest, and post-loan DTI before signing."
		},
		{
			property: "og:title",
			content: "Should I take this loan? · MoneyOS"
		},
		{
			property: "og:description",
			content: "Multi-step loan stress test with structured AI verdict."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter$1, "component")
});
//#endregion
//#region src/routes/decide.purchase.tsx
var $$splitComponentImporter = () => import("./decide.purchase-a-SY7PVj.js");
var Route = createFileRoute("/decide/purchase")({
	head: () => ({ meta: [
		{ title: "Can I buy this? · MoneyOS" },
		{
			name: "description",
			content: "Stress-test a purchase against your income, savings, and monthly obligations."
		},
		{
			property: "og:title",
			content: "Can I buy this? · MoneyOS"
		},
		{
			property: "og:description",
			content: "Structured multi-step check before you commit to a purchase."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter, "component")
});
//#endregion
//#region src/routeTree.gen.ts
var IndexRoute = Route$6.update({
	id: "/",
	path: "/",
	getParentRoute: () => Route$7
});
var ChatRoute = Route$5.update({
	id: "/chat",
	path: "/chat",
	getParentRoute: () => Route$7
});
var DashboardRoute = Route$4.update({
	id: "/dashboard",
	path: "/dashboard",
	getParentRoute: () => Route$7
});
var DecideRoute = Route$3.update({
	id: "/decide",
	path: "/decide",
	getParentRoute: () => Route$7
});
var ImportRoute = Route$2.update({
	id: "/import",
	path: "/import",
	getParentRoute: () => Route$7
});
var DecideRouteChildren = {
	DecideLoanRoute: Route$1.update({
		id: "/loan",
		path: "/loan",
		getParentRoute: () => DecideRoute
	}),
	DecidePurchaseRoute: Route.update({
		id: "/purchase",
		path: "/purchase",
		getParentRoute: () => DecideRoute
	})
};
var rootRouteChildren = {
	IndexRoute,
	ChatRoute,
	DashboardRoute,
	DecideRoute: DecideRoute._addFileChildren(DecideRouteChildren),
	ImportRoute
};
var routeTree = Route$7._addFileChildren(rootRouteChildren)._addFileTypes();
//#endregion
//#region src/router.tsx
var getRouter = () => {
	return createRouter({
		routeTree,
		context: { queryClient: new QueryClient() },
		scrollRestoration: true,
		defaultPreloadStaleTime: 0
	});
};
//#endregion
export { getRouter };
