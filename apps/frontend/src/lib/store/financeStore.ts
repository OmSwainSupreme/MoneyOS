import { create } from "zustand";
import type {
  Asset,
  BudgetEntry,
  Income,
  Liability,
  Transaction,
  TransactionCategory,
} from "@/types/finance";

interface FinanceState {
  transactions: Transaction[];
  assets: Asset[];
  liabilities: Liability[];
  budgets: BudgetEntry[];
  incomes: Income[];
}

interface FinanceActions {
  addTransactions: (rows: Transaction[]) => void;
  removeTransaction: (id: string) => void;
  addAsset: (asset: Asset) => void;
  removeAsset: (id: string) => void;
  addLiability: (liability: Liability) => void;
  removeLiability: (id: string) => void;
  upsertBudget: (entry: BudgetEntry) => void;
  upsertIncome: (income: Income) => void;
  clearAll: () => void;
}

const initialState: FinanceState = {
  transactions: [],
  assets: [],
  liabilities: [],
  budgets: [],
  incomes: [],
};

export const useFinanceStore = create<FinanceState & FinanceActions>((set) => ({
  ...initialState,
  addTransactions: (rows) =>
    set((s) => ({ transactions: [...s.transactions, ...rows] })),
  removeTransaction: (id) =>
    set((s) => ({ transactions: s.transactions.filter((t) => t.id !== id) })),
  addAsset: (asset) => set((s) => ({ assets: [...s.assets, asset] })),
  removeAsset: (id) => set((s) => ({ assets: s.assets.filter((a) => a.id !== id) })),
  addLiability: (liability) =>
    set((s) => ({ liabilities: [...s.liabilities, liability] })),
  removeLiability: (id) =>
    set((s) => ({ liabilities: s.liabilities.filter((l) => l.id !== id) })),
  upsertBudget: (entry) =>
    set((s) => {
      const idx = s.budgets.findIndex((b) => b.category === entry.category);
      const budgets = [...s.budgets];
      if (idx >= 0) budgets[idx] = entry;
      else budgets.push(entry);
      return { budgets };
    }),
  upsertIncome: (income) =>
    set((s) => {
      const idx = s.incomes.findIndex((i) => i.id === income.id);
      const incomes = [...s.incomes];
      if (idx >= 0) incomes[idx] = income;
      else incomes.push(income);
      return { incomes };
    }),
  clearAll: () => set({ ...initialState }),
}));

// ---------- Pure selectors ----------

export function selectMonthlyNetIncome(s: FinanceState): number {
  return s.incomes.reduce((sum, i) => {
    const monthly =
      i.cadence === "weekly"
        ? i.monthlyNet * (52 / 12)
        : i.cadence === "biweekly"
          ? i.monthlyNet * (26 / 12)
          : i.monthlyNet;
    return sum + monthly;
  }, 0);
}

export function selectMonthlyExpenses(s: FinanceState): number {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1).getTime();
  return s.transactions
    .filter((t) => new Date(t.date).getTime() >= start && t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);
}

export function selectNetCashFlow(s: FinanceState): number {
  return selectMonthlyNetIncome(s) - selectMonthlyExpenses(s);
}

export function selectSavingsRate(s: FinanceState): number {
  const income = selectMonthlyNetIncome(s);
  if (income <= 0) return 0;
  return Math.max(0, Math.min(1, selectNetCashFlow(s) / income));
}

export function selectDTI(s: FinanceState): number {
  const income = selectMonthlyNetIncome(s);
  if (income <= 0) return 0;
  const debt = s.liabilities.reduce((sum, l) => sum + l.minPayment, 0);
  return debt / income;
}

export function selectAssetLiabilityRatio(s: FinanceState): number {
  const assets = s.assets.reduce((sum, a) => sum + a.value, 0);
  const liabilities = s.liabilities.reduce((sum, l) => sum + l.principal, 0);
  if (liabilities <= 0) return assets > 0 ? Number.POSITIVE_INFINITY : 0;
  return assets / liabilities;
}

export interface BudgetUsageRow {
  category: TransactionCategory;
  limit: number;
  spent: number;
  pct: number;
}

export function selectBudgetUsage(s: FinanceState): BudgetUsageRow[] {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1).getTime();
  return s.budgets.map((b) => {
    const spent = s.transactions
      .filter(
        (t) =>
          t.category === b.category &&
          t.amount < 0 &&
          new Date(t.date).getTime() >= start,
      )
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);
    const pct = b.monthlyLimit > 0 ? spent / b.monthlyLimit : 0;
    return { category: b.category, limit: b.monthlyLimit, spent, pct };
  });
}

export interface CashflowPoint {
  date: string;
  net: number;
}

export function selectCashflowSeries(s: FinanceState, days = 30): CashflowPoint[] {
  const buckets = new Map<string, number>();
  const start = Date.now() - days * 24 * 60 * 60 * 1000;
  for (const t of s.transactions) {
    const time = new Date(t.date).getTime();
    if (time < start) continue;
    const day = new Date(time).toISOString().slice(0, 10);
    buckets.set(day, (buckets.get(day) ?? 0) + t.amount);
  }
  return [...buckets.entries()]
    .sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([date, net]) => ({ date, net }));
}
