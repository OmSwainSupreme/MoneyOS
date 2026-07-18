import { KpiCard } from "@/components/dashboard/KpiCard";
import {
  selectAssetLiabilityRatio,
  selectDTI,
  selectNetCashFlow,
  selectSavingsRate,
  useFinanceStore,
} from "@/lib/store/financeStore";

export function fmtCurrency(n: number): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

// Row of four KPI cards derived from the finance store selectors.
export function KpiGrid({ className }: { className?: string }) {
  const state = useFinanceStore();
  const netCashFlow = selectNetCashFlow(state);
  const savingsRate = selectSavingsRate(state);
  const dti = selectDTI(state);
  const alr = selectAssetLiabilityRatio(state);

  return (
    <div
      className={`grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 ${className ?? ""}`}
    >
      <KpiCard
        label="Net cash flow"
        value={fmtCurrency(netCashFlow)}
        tone={netCashFlow >= 0 ? "positive" : "danger"}
        hint="Income minus month-to-date expenses"
      />
      <KpiCard
        label="Savings rate"
        value={`${(savingsRate * 100).toFixed(0)}%`}
        tone={savingsRate >= 0.2 ? "positive" : "neutral"}
      />
      <KpiCard
        label="Debt-to-income"
        value={`${(dti * 100).toFixed(0)}%`}
        tone={dti > 0.36 ? "danger" : "neutral"}
      />
      <KpiCard
        label="Asset / liability"
        value={Number.isFinite(alr) ? alr.toFixed(2) : "∞"}
        tone={alr >= 1 ? "positive" : "neutral"}
      />
    </div>
  );
}
