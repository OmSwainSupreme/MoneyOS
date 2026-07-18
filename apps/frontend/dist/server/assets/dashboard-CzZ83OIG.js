import { a as selectNetCashFlow, c as Button, i as selectDTI, n as selectBudgetUsage, o as selectSavingsRate, r as selectCashflowSeries, s as useFinanceStore, t as selectAssetLiabilityRatio } from "./financeStore-wqInlGKf.js";
import { useEffect } from "react";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle } from "lucide-react";
//#region src/features/shared/mock/finance.ts
var DAY_MS = 1440 * 60 * 1e3;
function isoDaysAgo(daysAgo) {
	return (/* @__PURE__ */ new Date(Date.now() - daysAgo * DAY_MS)).toISOString();
}
function tx(daysAgo, amount, category, merchant) {
	return {
		id: crypto.randomUUID(),
		date: isoDaysAgo(daysAgo),
		amount,
		currency: "USD",
		category,
		merchant,
		source: "import"
	};
}
var mockFinanceSnapshot = {
	transactions: [
		tx(28, 4200, "income", "Acme Corp Payroll"),
		tx(14, 4200, "income", "Acme Corp Payroll"),
		tx(2, 120, "income", "Freelance gig"),
		tx(27, -1650, "housing", "Greenfield Apartments"),
		tx(13, -1650, "housing", "Greenfield Apartments"),
		tx(20, -320, "food", "Whole Foods"),
		tx(16, -210, "food", "Blue Bottle"),
		tx(10, -260, "food", "Trader Joe's"),
		tx(6, -240, "food", "DoorDash"),
		tx(2, -190, "food", "Local Bistro"),
		tx(25, -85, "transport", "Shell"),
		tx(18, -120, "transport", "Uber"),
		tx(9, -95, "transport", "Metro Card"),
		tx(22, -140, "utilities", "City Power"),
		tx(22, -65, "utilities", "AquaFlow"),
		tx(19, -45, "entertainment", "Spotify"),
		tx(12, -16, "entertainment", "Steam"),
		tx(7, -80, "entertainment", "AMC Theatres"),
		tx(17, -60, "health", "CVS Pharmacy"),
		tx(4, -35, "health", "Gym Membership"),
		tx(21, -130, "shopping", "Amazon"),
		tx(11, -75, "shopping", "Uniqlo"),
		tx(3, -210, "shopping", "Apple Store"),
		tx(15, -500, "savings", "Vanguard IRA"),
		tx(23, -310, "debt", "Chase Card"),
		tx(8, -240, "debt", "Discover"),
		tx(5, -42, "other", "Post Office")
	],
	assets: [
		{
			id: crypto.randomUUID(),
			name: "Everyday Checking",
			type: "cash",
			value: 6400,
			asOf: isoDaysAgo(1)
		},
		{
			id: crypto.randomUUID(),
			name: "High-Yield Savings",
			type: "cash",
			value: 18500,
			asOf: isoDaysAgo(1)
		},
		{
			id: crypto.randomUUID(),
			name: "Brokerage",
			type: "investment",
			value: 31200,
			asOf: isoDaysAgo(1)
		}
	],
	liabilities: [
		{
			id: crypto.randomUUID(),
			name: "Chase Sapphire",
			principal: 4200,
			apr: 21.99,
			termMonths: 36,
			minPayment: 160,
			startDate: isoDaysAgo(120)
		},
		{
			id: crypto.randomUUID(),
			name: "Discover It",
			principal: 2600,
			apr: 18.24,
			termMonths: 24,
			minPayment: 95,
			startDate: isoDaysAgo(90)
		},
		{
			id: crypto.randomUUID(),
			name: "Auto Loan",
			principal: 11200,
			apr: 5.49,
			termMonths: 48,
			minPayment: 265,
			startDate: isoDaysAgo(400)
		}
	],
	budgets: [
		{
			id: crypto.randomUUID(),
			category: "food",
			monthlyLimit: 700,
			rollover: false
		},
		{
			id: crypto.randomUUID(),
			category: "transport",
			monthlyLimit: 300,
			rollover: false
		},
		{
			id: crypto.randomUUID(),
			category: "entertainment",
			monthlyLimit: 150,
			rollover: false
		},
		{
			id: crypto.randomUUID(),
			category: "shopping",
			monthlyLimit: 400,
			rollover: false
		}
	],
	incomes: [{
		id: crypto.randomUUID(),
		source: "Acme Corp",
		monthlyNet: 4200,
		cadence: "monthly"
	}, {
		id: crypto.randomUUID(),
		source: "Freelance",
		monthlyNet: 180,
		cadence: "monthly"
	}]
};
//#endregion
//#region src/features/dashboard/mockData.ts
function getDashboardSeedData() {
	return mockFinanceSnapshot;
}
//#endregion
//#region src/features/dashboard/useDashboardData.ts
function useDashboardData() {
	const transactions = useFinanceStore((s) => s.transactions);
	const addTransactions = useFinanceStore((s) => s.addTransactions);
	const addAsset = useFinanceStore((s) => s.addAsset);
	const addLiability = useFinanceStore((s) => s.addLiability);
	const upsertBudget = useFinanceStore((s) => s.upsertBudget);
	const upsertIncome = useFinanceStore((s) => s.upsertIncome);
	const clearAll = useFinanceStore((s) => s.clearAll);
	const seeded = transactions.length > 0;
	const loadMockData = () => {
		const snap = getDashboardSeedData();
		addTransactions(snap.transactions);
		snap.assets.forEach(addAsset);
		snap.liabilities.forEach(addLiability);
		snap.budgets.forEach(upsertBudget);
		snap.incomes.forEach(upsertIncome);
	};
	useEffect(() => {
		if (transactions.length === 0) loadMockData();
	}, []);
	return {
		seeded,
		loadMockData,
		clearAll
	};
}
//#endregion
//#region src/components/dashboard/KpiCard.tsx
function KpiCard({ label, value, hint, tone = "neutral" }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "rounded-md border border-border bg-card p-4",
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "text-xs font-medium uppercase tracking-wide text-muted-foreground",
				children: label
			}),
			/* @__PURE__ */ jsx("div", {
				className: `mt-2 text-2xl font-semibold tabular-nums ${tone === "positive" ? "text-[color:var(--color-positive)]" : tone === "danger" ? "text-[color:var(--color-danger-zone)]" : "text-foreground"}`,
				children: value
			}),
			hint ? /* @__PURE__ */ jsx("div", {
				className: "mt-1 text-xs text-muted-foreground",
				children: hint
			}) : null
		]
	});
}
//#endregion
//#region src/features/dashboard/KpiGrid.tsx
function fmtCurrency(n) {
	return new Intl.NumberFormat(void 0, {
		style: "currency",
		currency: "USD",
		maximumFractionDigits: 0
	}).format(n);
}
function KpiGrid({ className }) {
	const state = useFinanceStore();
	const netCashFlow = selectNetCashFlow(state);
	const savingsRate = selectSavingsRate(state);
	const dti = selectDTI(state);
	const alr = selectAssetLiabilityRatio(state);
	return /* @__PURE__ */ jsxs("div", {
		className: `grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 ${className ?? ""}`,
		children: [
			/* @__PURE__ */ jsx(KpiCard, {
				label: "Net cash flow",
				value: fmtCurrency(netCashFlow),
				tone: netCashFlow >= 0 ? "positive" : "danger",
				hint: "Income minus month-to-date expenses"
			}),
			/* @__PURE__ */ jsx(KpiCard, {
				label: "Savings rate",
				value: `${(savingsRate * 100).toFixed(0)}%`,
				tone: savingsRate >= .2 ? "positive" : "neutral"
			}),
			/* @__PURE__ */ jsx(KpiCard, {
				label: "Debt-to-income",
				value: `${(dti * 100).toFixed(0)}%`,
				tone: dti > .36 ? "danger" : "neutral"
			}),
			/* @__PURE__ */ jsx(KpiCard, {
				label: "Asset / liability",
				value: Number.isFinite(alr) ? alr.toFixed(2) : "∞",
				tone: alr >= 1 ? "positive" : "neutral"
			})
		]
	});
}
//#endregion
//#region src/components/dashboard/CashflowChart.tsx
function CashflowChart({ data }) {
	const summary = data.length === 0 ? "No transactions in the last 30 days." : `Daily net cash flow across ${data.length} days, ranging from ${Math.min(...data.map((d) => d.net)).toFixed(2)} to ${Math.max(...data.map((d) => d.net)).toFixed(2)}.`;
	return /* @__PURE__ */ jsxs("div", {
		className: "rounded-md border border-border bg-card p-4",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "flex items-baseline justify-between",
				children: [/* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold text-card-foreground",
					children: "Cash flow (30 days)"
				}), /* @__PURE__ */ jsx("span", {
					className: "text-xs text-muted-foreground",
					children: "Daily net"
				})]
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-3 h-56 w-full",
				role: "img",
				"aria-label": summary,
				children: data.length === 0 ? /* @__PURE__ */ jsx(EmptyState, {}) : /* @__PURE__ */ jsx(ResponsiveContainer, {
					width: "100%",
					height: "100%",
					children: /* @__PURE__ */ jsxs(AreaChart, {
						data,
						margin: {
							top: 8,
							right: 8,
							left: 0,
							bottom: 0
						},
						children: [
							/* @__PURE__ */ jsx("defs", { children: /* @__PURE__ */ jsxs("linearGradient", {
								id: "cashflowFill",
								x1: "0",
								y1: "0",
								x2: "0",
								y2: "1",
								children: [/* @__PURE__ */ jsx("stop", {
									offset: "0%",
									stopColor: "var(--color-positive)",
									stopOpacity: .4
								}), /* @__PURE__ */ jsx("stop", {
									offset: "100%",
									stopColor: "var(--color-positive)",
									stopOpacity: 0
								})]
							}) }),
							/* @__PURE__ */ jsx(XAxis, {
								dataKey: "date",
								tick: {
									fontSize: 11,
									fill: "var(--color-muted-foreground)"
								}
							}),
							/* @__PURE__ */ jsx(YAxis, { tick: {
								fontSize: 11,
								fill: "var(--color-muted-foreground)"
							} }),
							/* @__PURE__ */ jsx(Tooltip, { contentStyle: {
								background: "var(--color-popover)",
								color: "var(--color-popover-foreground)",
								border: "1px solid var(--color-border)",
								borderRadius: 6,
								fontSize: 12
							} }),
							/* @__PURE__ */ jsx(Area, {
								type: "monotone",
								dataKey: "net",
								stroke: "var(--color-positive)",
								strokeWidth: 2,
								fill: "url(#cashflowFill)",
								isAnimationActive: false
							})
						]
					})
				})
			}),
			/* @__PURE__ */ jsxs("table", {
				className: "sr-only",
				children: [
					/* @__PURE__ */ jsx("caption", { children: "Daily net cash flow, last 30 days" }),
					/* @__PURE__ */ jsx("thead", { children: /* @__PURE__ */ jsxs("tr", { children: [/* @__PURE__ */ jsx("th", {
						scope: "col",
						children: "Date"
					}), /* @__PURE__ */ jsx("th", {
						scope: "col",
						children: "Net"
					})] }) }),
					/* @__PURE__ */ jsx("tbody", { children: data.map((d) => /* @__PURE__ */ jsxs("tr", { children: [/* @__PURE__ */ jsx("td", { children: d.date }), /* @__PURE__ */ jsx("td", { children: d.net.toFixed(2) })] }, d.date)) })
				]
			})
		]
	});
}
function EmptyState() {
	return /* @__PURE__ */ jsx("div", {
		className: "flex h-full items-center justify-center text-sm text-muted-foreground",
		children: "Import a statement to populate this chart."
	});
}
//#endregion
//#region src/features/dashboard/CashflowPanel.tsx
function CashflowPanel({ days = 30, className }) {
	return /* @__PURE__ */ jsx("div", {
		className,
		children: /* @__PURE__ */ jsx(CashflowChart, { data: selectCashflowSeries(useFinanceStore(), days) })
	});
}
//#endregion
//#region src/components/dashboard/OverspendAlarmZone.tsx
function OverspendAlarmZone({ rows }) {
	const overspent = rows.filter((r) => r.pct >= 1);
	return /* @__PURE__ */ jsxs("div", {
		className: "rounded-md border border-border bg-card p-4",
		children: [/* @__PURE__ */ jsx("h2", {
			className: "text-sm font-semibold text-card-foreground",
			children: "Overspend alarms"
		}), rows.length === 0 ? /* @__PURE__ */ jsx("p", {
			className: "mt-2 text-sm text-muted-foreground",
			children: "No budgets defined yet. Add category limits to enable overspend detection."
		}) : /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("ul", {
			"aria-live": "polite",
			className: "mt-3 space-y-2",
			children: rows.map((row) => {
				const over = row.pct >= 1;
				const pctText = `${(row.pct * 100).toFixed(0)}%`;
				return /* @__PURE__ */ jsxs("li", {
					className: "text-sm",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "flex items-center justify-between",
						children: [/* @__PURE__ */ jsx("span", {
							className: "capitalize text-foreground",
							children: row.category
						}), /* @__PURE__ */ jsxs("span", {
							className: "tabular-nums text-muted-foreground",
							children: [
								row.spent.toFixed(2),
								" / ",
								row.limit.toFixed(2),
								" · ",
								pctText
							]
						})]
					}), /* @__PURE__ */ jsx("div", {
						className: "mt-1 h-2 w-full overflow-hidden rounded-md bg-muted",
						role: "progressbar",
						"aria-valuemin": 0,
						"aria-valuemax": 100,
						"aria-valuenow": Math.min(100, Math.round(row.pct * 100)),
						"aria-label": `${row.category} budget usage`,
						children: /* @__PURE__ */ jsx("div", {
							className: "h-full",
							style: {
								width: `${Math.min(100, row.pct * 100).toFixed(1)}%`,
								backgroundColor: over ? "var(--color-danger-zone)" : "var(--color-positive)"
							}
						})
					})]
				}, row.category);
			})
		}), overspent.length > 0 ? /* @__PURE__ */ jsxs("div", {
			role: "alert",
			className: "mt-3 flex items-start gap-2 rounded-md border border-[color:var(--color-danger-zone)]/40 bg-[color:var(--color-danger-zone)]/10 p-2 text-sm text-[color:var(--color-danger-zone)]",
			children: [/* @__PURE__ */ jsx(AlertTriangle, {
				"aria-hidden": true,
				className: "mt-0.5 h-4 w-4"
			}), /* @__PURE__ */ jsxs("span", { children: [
				overspent.length,
				" categor",
				overspent.length === 1 ? "y is" : "ies are",
				" ",
				"over budget this month."
			] })]
		}) : null] })]
	});
}
//#endregion
//#region src/features/dashboard/BudgetPanel.tsx
function BudgetPanel({ className }) {
	return /* @__PURE__ */ jsx("div", {
		className,
		children: /* @__PURE__ */ jsx(OverspendAlarmZone, { rows: selectBudgetUsage(useFinanceStore()) })
	});
}
//#endregion
//#region src/components/dashboard/RecentTransactionsTable.tsx
function RecentTransactionsTable({ rows }) {
	const latest = [...rows].sort((a, b) => a.date < b.date ? 1 : -1).slice(0, 20);
	return /* @__PURE__ */ jsxs("div", {
		className: "rounded-md border border-border bg-card p-4",
		children: [/* @__PURE__ */ jsx("h2", {
			className: "text-sm font-semibold text-card-foreground",
			children: "Recent transactions"
		}), latest.length === 0 ? /* @__PURE__ */ jsx("p", {
			className: "mt-2 text-sm text-muted-foreground",
			children: "Import a statement to see transactions here."
		}) : /* @__PURE__ */ jsx("div", {
			className: "mt-3 overflow-x-auto",
			children: /* @__PURE__ */ jsxs("table", {
				className: "w-full text-sm",
				children: [/* @__PURE__ */ jsx("thead", { children: /* @__PURE__ */ jsxs("tr", {
					className: "border-b border-border text-left text-muted-foreground",
					children: [
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "py-2 pr-2 font-medium",
							children: "Date"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "py-2 pr-2 font-medium",
							children: "Merchant"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "py-2 pr-2 font-medium",
							children: "Category"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "py-2 text-right font-medium",
							children: "Amount"
						})
					]
				}) }), /* @__PURE__ */ jsx("tbody", { children: latest.map((t) => /* @__PURE__ */ jsxs("tr", {
					className: "border-b border-border last:border-0",
					children: [
						/* @__PURE__ */ jsx("td", {
							className: "py-2 pr-2 text-muted-foreground tabular-nums",
							children: t.date.slice(0, 10)
						}),
						/* @__PURE__ */ jsx("td", {
							className: "py-2 pr-2 text-foreground",
							children: t.merchant || "—"
						}),
						/* @__PURE__ */ jsx("td", {
							className: "py-2 pr-2 capitalize text-muted-foreground",
							children: t.category
						}),
						/* @__PURE__ */ jsx("td", {
							className: `py-2 text-right tabular-nums ${t.amount < 0 ? "text-[color:var(--color-danger-zone)]" : "text-[color:var(--color-positive)]"}`,
							children: t.amount.toFixed(2)
						})
					]
				}, t.id)) })]
			})
		})]
	});
}
//#endregion
//#region src/features/dashboard/TransactionsPanel.tsx
function TransactionsPanel({ className }) {
	return /* @__PURE__ */ jsx("div", {
		className,
		children: /* @__PURE__ */ jsx(RecentTransactionsTable, { rows: useFinanceStore().transactions })
	});
}
//#endregion
//#region src/routes/dashboard.tsx?tsr-split=component
function DashboardPage() {
	const { seeded, loadMockData, clearAll } = useDashboardData();
	return /* @__PURE__ */ jsxs("div", {
		className: "mx-auto max-w-6xl px-4 py-8 sm:px-6",
		children: [/* @__PURE__ */ jsxs("header", {
			className: "mb-6 flex flex-wrap items-start justify-between gap-3",
			children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h1", {
				className: "text-2xl font-semibold tracking-tight text-foreground",
				children: "Dashboard"
			}), /* @__PURE__ */ jsx("p", {
				className: "text-sm text-muted-foreground",
				children: "Session-scoped snapshot of your finances."
			})] }), /* @__PURE__ */ jsx("div", {
				className: "flex flex-wrap gap-2",
				children: !seeded ? /* @__PURE__ */ jsx(Button, {
					onClick: loadMockData,
					variant: "default",
					children: "Load sample data"
				}) : /* @__PURE__ */ jsx(Button, {
					onClick: () => clearAll(),
					variant: "outline",
					children: "Clear"
				})
			})]
		}), /* @__PURE__ */ jsxs("div", {
			className: "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-12",
			children: [
				/* @__PURE__ */ jsx("div", {
					className: "lg:col-span-12",
					children: /* @__PURE__ */ jsx(KpiGrid, {})
				}),
				/* @__PURE__ */ jsx("div", {
					className: "lg:col-span-8",
					children: /* @__PURE__ */ jsx(CashflowPanel, {})
				}),
				/* @__PURE__ */ jsx("div", {
					className: "lg:col-span-4",
					children: /* @__PURE__ */ jsx(BudgetPanel, {})
				}),
				/* @__PURE__ */ jsx("div", {
					className: "lg:col-span-12",
					children: /* @__PURE__ */ jsx(TransactionsPanel, {})
				})
			]
		})]
	});
}
//#endregion
export { DashboardPage as component };
