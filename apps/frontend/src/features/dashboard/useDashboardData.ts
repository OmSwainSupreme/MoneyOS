// Hydrates the global finance store from mock seed data so the dashboard
// renders populated on first load. Idempotent: only seeds when the store
// holds no transactions yet.

import { useEffect } from "react";
import { useFinanceStore } from "@/lib/store/financeStore";
import { getDashboardSeedData } from "./mockData";

export function useDashboardData() {
  const transactions = useFinanceStore((s) => s.transactions);
  const addTransactions = useFinanceStore((s) => s.addTransactions);
  const addAsset = useFinanceStore((s) => s.addAsset);
  const addLiability = useFinanceStore((s) => s.addLiability);
  const upsertBudget = useFinanceStore((s) => s.upsertBudget);
  const upsertIncome = useFinanceStore((s) => s.upsertIncome);
  const clearAll = useFinanceStore((s) => s.clearAll);

  const seeded = transactions.length > 0;

  const loadMockData = () => {
    // TODO(backend): stream the snapshot from the server instead of
    // seeding client-side once the finance API is available.
    const snap = getDashboardSeedData();
    addTransactions(snap.transactions);
    snap.assets.forEach(addAsset);
    snap.liabilities.forEach(addLiability);
    snap.budgets.forEach(upsertBudget);
    snap.incomes.forEach(upsertIncome);
  };

  // Auto-seed once on mount when the store is empty.
  useEffect(() => {
    if (transactions.length === 0) loadMockData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { seeded, loadMockData, clearAll };
}
