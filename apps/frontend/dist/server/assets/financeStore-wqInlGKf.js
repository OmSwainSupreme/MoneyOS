import * as React from "react";
import { jsx } from "react/jsx-runtime";
import { create } from "zustand";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
//#region src/lib/utils.ts
function cn(...inputs) {
	return twMerge(clsx(inputs));
}
//#endregion
//#region src/components/ui/button.tsx
var buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0", {
	variants: {
		variant: {
			default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
			destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
			outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
			secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
			ghost: "hover:bg-accent hover:text-accent-foreground",
			link: "text-primary underline-offset-4 hover:underline"
		},
		size: {
			default: "h-9 px-4 py-2",
			sm: "h-8 rounded-md px-3 text-xs",
			lg: "h-10 rounded-md px-8",
			icon: "h-9 w-9"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
var Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
	return /* @__PURE__ */ jsx(asChild ? Slot : "button", {
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		ref,
		...props
	});
});
Button.displayName = "Button";
//#endregion
//#region src/lib/store/financeStore.ts
var initialState = {
	transactions: [],
	assets: [],
	liabilities: [],
	budgets: [],
	incomes: []
};
var useFinanceStore = create((set) => ({
	...initialState,
	addTransactions: (rows) => set((s) => ({ transactions: [...s.transactions, ...rows] })),
	removeTransaction: (id) => set((s) => ({ transactions: s.transactions.filter((t) => t.id !== id) })),
	addAsset: (asset) => set((s) => ({ assets: [...s.assets, asset] })),
	removeAsset: (id) => set((s) => ({ assets: s.assets.filter((a) => a.id !== id) })),
	addLiability: (liability) => set((s) => ({ liabilities: [...s.liabilities, liability] })),
	removeLiability: (id) => set((s) => ({ liabilities: s.liabilities.filter((l) => l.id !== id) })),
	upsertBudget: (entry) => set((s) => {
		const idx = s.budgets.findIndex((b) => b.category === entry.category);
		const budgets = [...s.budgets];
		if (idx >= 0) budgets[idx] = entry;
		else budgets.push(entry);
		return { budgets };
	}),
	upsertIncome: (income) => set((s) => {
		const idx = s.incomes.findIndex((i) => i.id === income.id);
		const incomes = [...s.incomes];
		if (idx >= 0) incomes[idx] = income;
		else incomes.push(income);
		return { incomes };
	}),
	clearAll: () => set({ ...initialState })
}));
function selectMonthlyNetIncome(s) {
	return s.incomes.reduce((sum, i) => {
		return sum + (i.cadence === "weekly" ? i.monthlyNet * (52 / 12) : i.cadence === "biweekly" ? i.monthlyNet * (26 / 12) : i.monthlyNet);
	}, 0);
}
function selectMonthlyExpenses(s) {
	const now = /* @__PURE__ */ new Date();
	const start = new Date(now.getFullYear(), now.getMonth(), 1).getTime();
	return s.transactions.filter((t) => new Date(t.date).getTime() >= start && t.amount < 0).reduce((sum, t) => sum + Math.abs(t.amount), 0);
}
function selectNetCashFlow(s) {
	return selectMonthlyNetIncome(s) - selectMonthlyExpenses(s);
}
function selectSavingsRate(s) {
	const income = selectMonthlyNetIncome(s);
	if (income <= 0) return 0;
	return Math.max(0, Math.min(1, selectNetCashFlow(s) / income));
}
function selectDTI(s) {
	const income = selectMonthlyNetIncome(s);
	if (income <= 0) return 0;
	return s.liabilities.reduce((sum, l) => sum + l.minPayment, 0) / income;
}
function selectAssetLiabilityRatio(s) {
	const assets = s.assets.reduce((sum, a) => sum + a.value, 0);
	const liabilities = s.liabilities.reduce((sum, l) => sum + l.principal, 0);
	if (liabilities <= 0) return assets > 0 ? Number.POSITIVE_INFINITY : 0;
	return assets / liabilities;
}
function selectBudgetUsage(s) {
	const now = /* @__PURE__ */ new Date();
	const start = new Date(now.getFullYear(), now.getMonth(), 1).getTime();
	return s.budgets.map((b) => {
		const spent = s.transactions.filter((t) => t.category === b.category && t.amount < 0 && new Date(t.date).getTime() >= start).reduce((sum, t) => sum + Math.abs(t.amount), 0);
		const pct = b.monthlyLimit > 0 ? spent / b.monthlyLimit : 0;
		return {
			category: b.category,
			limit: b.monthlyLimit,
			spent,
			pct
		};
	});
}
function selectCashflowSeries(s, days = 30) {
	const buckets = /* @__PURE__ */ new Map();
	const start = Date.now() - days * 24 * 60 * 60 * 1e3;
	for (const t of s.transactions) {
		const time = new Date(t.date).getTime();
		if (time < start) continue;
		const day = new Date(time).toISOString().slice(0, 10);
		buckets.set(day, (buckets.get(day) ?? 0) + t.amount);
	}
	return [...buckets.entries()].sort(([a], [b]) => a < b ? -1 : 1).map(([date, net]) => ({
		date,
		net
	}));
}
//#endregion
export { selectNetCashFlow as a, Button as c, selectDTI as i, selectBudgetUsage as n, selectSavingsRate as o, selectCashflowSeries as r, useFinanceStore as s, selectAssetLiabilityRatio as t };
