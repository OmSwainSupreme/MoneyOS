import { d as TSS_SERVER_FUNCTION, t as createServerFn } from "./createServerFn-D40y8WyT.js";
import { i as PurchaseDecisionInputSchema, r as LoanDecisionInputSchema, t as DecisionInputSchema } from "./finance-BjdKDlHX.js";
import { t as getServerFnById } from "./__23tanstack-start-server-fn-resolver-DrHim1Zj.js";
import * as React from "react";
import { useState } from "react";
import { isRedirect, useRouter } from "@tanstack/react-router";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
//#region ../../node_modules/@tanstack/react-start/dist/esm/useServerFn.js
function useServerFn(serverFn) {
	const router = useRouter();
	return React.useCallback(async (...args) => {
		try {
			const res = await serverFn(...args);
			if (isRedirect(res)) throw res;
			return res;
		} catch (err) {
			if (isRedirect(err)) {
				err.options._fromLocation = router.stores.location.get();
				return router.navigate(router.resolveRedirect(err).options);
			}
			throw err;
		}
	}, [router, serverFn]);
}
//#endregion
//#region ../../node_modules/@tanstack/start-server-core/dist/esm/createSsrRpc.js
var createSsrRpc = (functionId) => {
	const url = "/_serverFn/" + functionId;
	const serverFnMeta = { id: functionId };
	const fn = async (...args) => {
		return (await getServerFnById(functionId, { origin: "server" }))(...args);
	};
	return Object.assign(fn, {
		url,
		serverFnMeta,
		[TSS_SERVER_FUNCTION]: true
	});
};
//#endregion
//#region src/lib/decision.functions.ts
var analyzeDecision = createServerFn({ method: "POST" }).inputValidator((raw) => DecisionInputSchema.parse(raw)).handler(createSsrRpc("c90455b75509e343d8ff38c8f80c3279564e3028cdfe7da2fa885c25938b116e"));
//#endregion
//#region src/components/decide/Wizard.tsx
function DecisionWizard({ title, description, steps, buildInput }) {
	const [current, setCurrent] = useState(0);
	const [values, setValues] = useState({});
	const [verdict, setVerdict] = useState(null);
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState(null);
	const analyze = useServerFn(analyzeDecision);
	const step = steps[current];
	const isLast = current === steps.length - 1;
	const handleStepSubmit = async (stepValues) => {
		const merged = {
			...values,
			...stepValues
		};
		setValues(merged);
		if (!isLast) {
			setCurrent((c) => c + 1);
			return;
		}
		setSubmitting(true);
		setError(null);
		try {
			const input = buildInput(merged);
			const result = await analyze({ data: input });
			setVerdict(result);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Analysis failed.");
		} finally {
			setSubmitting(false);
		}
	};
	if (verdict) {
		const tone = verdict.verdict === "yes" ? "text-[color:var(--color-positive)]" : verdict.verdict === "no" ? "text-[color:var(--color-danger-zone)]" : "text-foreground";
		return /* @__PURE__ */ jsxs("div", {
			className: "mx-auto max-w-2xl px-4 py-8 sm:px-6",
			children: [/* @__PURE__ */ jsx("h1", {
				className: "text-2xl font-semibold tracking-tight text-foreground",
				children: title
			}), /* @__PURE__ */ jsxs("div", {
				className: "mt-6 rounded-md border border-border bg-card p-6",
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: `text-xs font-medium uppercase tracking-wide ${tone}`,
						children: ["Verdict: ", verdict.verdict]
					}),
					/* @__PURE__ */ jsx("h2", {
						className: `mt-2 text-xl font-semibold ${tone}`,
						children: verdict.headline
					}),
					/* @__PURE__ */ jsx("p", {
						className: "mt-3 text-sm text-foreground",
						children: verdict.rationale
					}),
					/* @__PURE__ */ jsxs("dl", {
						className: "mt-4 grid grid-cols-2 gap-3 text-sm",
						children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", {
							className: "text-muted-foreground",
							children: "Monthly impact"
						}), /* @__PURE__ */ jsx("dd", {
							className: "tabular-nums text-foreground",
							children: verdict.monthlyImpact.toFixed(2)
						})] }), /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("dt", {
							className: "text-muted-foreground",
							children: "Savings runway"
						}), /* @__PURE__ */ jsxs("dd", {
							className: "tabular-nums text-foreground",
							children: [verdict.savingsRunwayMonths.toFixed(1), " months"]
						})] })]
					}),
					/* @__PURE__ */ jsx("button", {
						type: "button",
						onClick: () => {
							setVerdict(null);
							setValues({});
							setCurrent(0);
						},
						className: "mt-6 inline-flex min-h-11 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground hover:bg-accent",
						children: "Start over"
					})
				]
			})]
		});
	}
	return /* @__PURE__ */ jsxs("div", {
		className: "mx-auto max-w-2xl px-4 py-8 sm:px-6",
		children: [
			/* @__PURE__ */ jsxs("header", {
				className: "mb-6",
				children: [/* @__PURE__ */ jsx("h1", {
					className: "text-2xl font-semibold tracking-tight text-foreground",
					children: title
				}), /* @__PURE__ */ jsx("p", {
					className: "text-sm text-muted-foreground",
					children: description
				})]
			}),
			/* @__PURE__ */ jsx("ol", {
				className: "mb-4 flex items-center gap-3 text-xs text-muted-foreground",
				"aria-label": "Progress",
				children: steps.map((s, i) => /* @__PURE__ */ jsxs("li", {
					className: "flex items-center gap-2",
					children: [/* @__PURE__ */ jsx("span", {
						className: `inline-flex h-6 w-6 items-center justify-center rounded-md tabular-nums ${i === current ? "bg-primary text-primary-foreground" : i < current ? "bg-accent text-accent-foreground" : "border border-border"}`,
						"aria-current": i === current ? "step" : void 0,
						children: i + 1
					}), /* @__PURE__ */ jsx("span", {
						className: i === current ? "font-medium text-foreground" : "",
						children: s.title
					})]
				}, s.key))
			}),
			/* @__PURE__ */ jsx(StepForm, {
				step,
				initialValues: values,
				canGoBack: current > 0,
				isLast,
				submitting,
				error,
				onBack: () => setCurrent((c) => Math.max(0, c - 1)),
				onSubmit: handleStepSubmit
			}, step.key)
		]
	});
}
function StepForm({ step, initialValues, canGoBack, isLast, submitting, error, onBack, onSubmit }) {
	const form = useForm({
		resolver: zodResolver(step.schema),
		defaultValues: {
			...step.defaultValues,
			...initialValues
		},
		mode: "onChange"
	});
	return /* @__PURE__ */ jsxs("form", {
		onSubmit: form.handleSubmit(async (v) => {
			await onSubmit(v);
		}),
		noValidate: true,
		className: "rounded-md border border-border bg-card p-4",
		children: [
			step.render(form),
			error ? /* @__PURE__ */ jsx("p", {
				role: "alert",
				className: "mt-3 text-sm text-[color:var(--color-danger-zone)]",
				children: error
			}) : null,
			/* @__PURE__ */ jsxs("div", {
				className: "mt-4 flex items-center justify-between",
				children: [/* @__PURE__ */ jsx("button", {
					type: "button",
					onClick: onBack,
					disabled: !canGoBack,
					className: "inline-flex min-h-11 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground hover:bg-accent disabled:opacity-50",
					children: "Back"
				}), /* @__PURE__ */ jsx("button", {
					type: "submit",
					disabled: !form.formState.isValid || submitting,
					className: "inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50",
					children: isLast ? submitting ? "Analyzing…" : "Analyze" : "Next"
				})]
			})
		]
	});
}
function Field({ label, htmlFor, error, children }) {
	const errId = `${htmlFor}-error`;
	return /* @__PURE__ */ jsxs("div", {
		className: "mb-3",
		children: [
			/* @__PURE__ */ jsx("label", {
				htmlFor,
				className: "block text-sm font-medium text-foreground",
				children: label
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-1",
				children
			}),
			error ? /* @__PURE__ */ jsx("p", {
				id: errId,
				role: "alert",
				className: "mt-1 text-xs text-[color:var(--color-danger-zone)]",
				children: error
			}) : null
		]
	});
}
//#endregion
//#region src/features/decide/seeds.ts
var purchaseSeed = {
	itemName: "New laptop",
	price: 1200,
	urgency: "3m",
	paymentMethod: "credit",
	monthlyNetIncome: 4200,
	monthlyFixedExpenses: 2600,
	liquidSavings: 9e3,
	emergencyFundMonths: 4
};
var loanSeed = {
	principal: 15e3,
	apr: 6.5,
	termMonths: 48,
	purpose: "Car refinance",
	existingMonthlyDebt: 400,
	monthlyNetIncome: 4200,
	liquidSavings: 9e3
};
//#endregion
//#region src/features/decide/PurchaseWizard.tsx
var step1 = z.object({
	itemName: z.string().trim().min(1, "Required").max(120),
	price: z.coerce.number().finite().positive("Must be positive"),
	urgency: z.enum([
		"now",
		"3m",
		"12m"
	])
});
var step2 = z.object({
	paymentMethod: z.enum([
		"cash",
		"credit",
		"financing"
	]),
	apr: z.coerce.number().finite().min(0).max(100).optional(),
	termMonths: z.coerce.number().int().min(1).max(600).optional()
}).superRefine((val, ctx) => {
	if (val.paymentMethod === "financing") {
		if (val.apr === void 0 || Number.isNaN(val.apr)) ctx.addIssue({
			code: "custom",
			path: ["apr"],
			message: "APR required"
		});
		if (val.termMonths === void 0 || Number.isNaN(val.termMonths)) ctx.addIssue({
			code: "custom",
			path: ["termMonths"],
			message: "Term required"
		});
	}
});
var step3 = z.object({
	monthlyNetIncome: z.coerce.number().finite().nonnegative(),
	monthlyFixedExpenses: z.coerce.number().finite().nonnegative(),
	liquidSavings: z.coerce.number().finite().nonnegative(),
	emergencyFundMonths: z.coerce.number().finite().min(0).max(60)
});
var steps$1 = [
	{
		key: "item",
		title: "Item",
		schema: step1,
		defaultValues: {
			itemName: purchaseSeed.itemName ?? "",
			price: purchaseSeed.price ?? 0,
			urgency: purchaseSeed.urgency ?? "3m"
		},
		render: (form) => /* @__PURE__ */ jsxs(Fragment, { children: [
			/* @__PURE__ */ jsx(Field, {
				label: "Item name",
				htmlFor: "itemName",
				error: form.formState.errors.itemName?.message,
				children: /* @__PURE__ */ jsx("input", {
					id: "itemName",
					...form.register("itemName"),
					"aria-invalid": !!form.formState.errors.itemName,
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
				})
			}),
			/* @__PURE__ */ jsx(Field, {
				label: "Price",
				htmlFor: "price",
				error: form.formState.errors.price?.message,
				children: /* @__PURE__ */ jsx("input", {
					id: "price",
					type: "number",
					step: "0.01",
					...form.register("price"),
					"aria-invalid": !!form.formState.errors.price,
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
				})
			}),
			/* @__PURE__ */ jsx(Field, {
				label: "Urgency",
				htmlFor: "urgency",
				children: /* @__PURE__ */ jsxs("select", {
					id: "urgency",
					...form.register("urgency"),
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
					children: [
						/* @__PURE__ */ jsx("option", {
							value: "now",
							children: "Now"
						}),
						/* @__PURE__ */ jsx("option", {
							value: "3m",
							children: "Within 3 months"
						}),
						/* @__PURE__ */ jsx("option", {
							value: "12m",
							children: "Within 12 months"
						})
					]
				})
			})
		] })
	},
	{
		key: "funding",
		title: "Funding",
		schema: step2,
		defaultValues: { paymentMethod: purchaseSeed.paymentMethod ?? "cash" },
		render: (form) => {
			const method = form.watch("paymentMethod");
			return /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx(Field, {
				label: "Payment method",
				htmlFor: "paymentMethod",
				children: /* @__PURE__ */ jsxs("select", {
					id: "paymentMethod",
					...form.register("paymentMethod"),
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
					children: [
						/* @__PURE__ */ jsx("option", {
							value: "cash",
							children: "Cash"
						}),
						/* @__PURE__ */ jsx("option", {
							value: "credit",
							children: "Credit card (paid in full)"
						}),
						/* @__PURE__ */ jsx("option", {
							value: "financing",
							children: "Financing"
						})
					]
				})
			}), method === "financing" ? /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx(Field, {
				label: "APR (%)",
				htmlFor: "apr",
				error: form.formState.errors.apr?.message,
				children: /* @__PURE__ */ jsx("input", {
					id: "apr",
					type: "number",
					step: "0.01",
					...form.register("apr"),
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
				})
			}), /* @__PURE__ */ jsx(Field, {
				label: "Term (months)",
				htmlFor: "termMonths",
				error: form.formState.errors.termMonths?.message,
				children: /* @__PURE__ */ jsx("input", {
					id: "termMonths",
					type: "number",
					step: "1",
					...form.register("termMonths"),
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
				})
			})] }) : null] });
		}
	},
	{
		key: "context",
		title: "You",
		schema: step3,
		defaultValues: {
			monthlyNetIncome: purchaseSeed.monthlyNetIncome ?? 0,
			monthlyFixedExpenses: purchaseSeed.monthlyFixedExpenses ?? 0,
			liquidSavings: purchaseSeed.liquidSavings ?? 0,
			emergencyFundMonths: purchaseSeed.emergencyFundMonths ?? 3
		},
		render: (form) => /* @__PURE__ */ jsx(Fragment, { children: [
			["monthlyNetIncome", "Monthly net income"],
			["monthlyFixedExpenses", "Monthly fixed expenses"],
			["liquidSavings", "Liquid savings"],
			["emergencyFundMonths", "Emergency fund (months)"]
		].map(([name, label]) => /* @__PURE__ */ jsx(Field, {
			label,
			htmlFor: name,
			error: form.formState.errors[name]?.message ?? void 0,
			children: /* @__PURE__ */ jsx("input", {
				id: name,
				type: "number",
				step: "0.01",
				...form.register(name),
				className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
			})
		}, name)) })
	}
];
function PurchaseWizard({ className }) {
	const buildInput = (values) => {
		return PurchaseDecisionInputSchema.parse({
			kind: "purchase",
			...values
		});
	};
	return /* @__PURE__ */ jsx("div", {
		className,
		children: /* @__PURE__ */ jsx(DecisionWizard, {
			title: "Can I buy this?",
			description: "Multi-step check against income, savings, and monthly obligations.",
			steps: steps$1,
			buildInput
		})
	});
}
//#endregion
//#region src/features/decide/LoanWizard.tsx
var stepLoan = z.object({
	principal: z.coerce.number().finite().positive(),
	apr: z.coerce.number().finite().min(0).max(100),
	termMonths: z.coerce.number().int().min(1).max(600),
	purpose: z.string().trim().min(1).max(200)
});
var stepBudget = z.object({
	existingMonthlyDebt: z.coerce.number().finite().nonnegative(),
	monthlyNetIncome: z.coerce.number().finite().nonnegative(),
	liquidSavings: z.coerce.number().finite().nonnegative()
});
var steps = [{
	key: "loan",
	title: "Loan",
	schema: stepLoan,
	defaultValues: {
		principal: loanSeed.principal ?? 0,
		apr: loanSeed.apr ?? 0,
		termMonths: loanSeed.termMonths ?? 12,
		purpose: loanSeed.purpose ?? ""
	},
	render: (form) => /* @__PURE__ */ jsxs(Fragment, { children: [
		/* @__PURE__ */ jsx(Field, {
			label: "Principal",
			htmlFor: "principal",
			error: form.formState.errors.principal?.message,
			children: /* @__PURE__ */ jsx("input", {
				id: "principal",
				type: "number",
				step: "0.01",
				...form.register("principal"),
				className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
			})
		}),
		/* @__PURE__ */ jsx(Field, {
			label: "APR (%)",
			htmlFor: "apr",
			error: form.formState.errors.apr?.message,
			children: /* @__PURE__ */ jsx("input", {
				id: "apr",
				type: "number",
				step: "0.01",
				...form.register("apr"),
				className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
			})
		}),
		/* @__PURE__ */ jsx(Field, {
			label: "Term (months)",
			htmlFor: "termMonths",
			error: form.formState.errors.termMonths?.message,
			children: /* @__PURE__ */ jsx("input", {
				id: "termMonths",
				type: "number",
				step: "1",
				...form.register("termMonths"),
				className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
			})
		}),
		/* @__PURE__ */ jsx(Field, {
			label: "Purpose",
			htmlFor: "purpose",
			error: form.formState.errors.purpose?.message,
			children: /* @__PURE__ */ jsx("input", {
				id: "purpose",
				...form.register("purpose"),
				className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
			})
		})
	] })
}, {
	key: "budget",
	title: "Budget",
	schema: stepBudget,
	defaultValues: {
		existingMonthlyDebt: loanSeed.existingMonthlyDebt ?? 0,
		monthlyNetIncome: loanSeed.monthlyNetIncome ?? 0,
		liquidSavings: loanSeed.liquidSavings ?? 0
	},
	render: (form) => /* @__PURE__ */ jsx(Fragment, { children: [
		["existingMonthlyDebt", "Existing monthly debt payments"],
		["monthlyNetIncome", "Monthly net income"],
		["liquidSavings", "Liquid savings"]
	].map(([name, label]) => /* @__PURE__ */ jsx(Field, {
		label,
		htmlFor: name,
		error: form.formState.errors[name]?.message ?? void 0,
		children: /* @__PURE__ */ jsx("input", {
			id: name,
			type: "number",
			step: "0.01",
			...form.register(name),
			className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
		})
	}, name)) })
}];
function LoanWizard({ className }) {
	const buildInput = (values) => {
		return LoanDecisionInputSchema.parse({
			kind: "loan",
			...values
		});
	};
	return /* @__PURE__ */ jsx("div", {
		className,
		children: /* @__PURE__ */ jsx(DecisionWizard, {
			title: "Should I take this loan?",
			description: "Two-step check for monthly impact, DTI, and runway.",
			steps,
			buildInput
		})
	});
}
//#endregion
export { PurchaseWizard as n, LoanWizard as t };
