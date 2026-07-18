import { createFileRoute } from "@tanstack/react-router";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { CashflowChart } from "@/components/dashboard/CashflowChart";
import { OverspendAlarmZone } from "@/components/dashboard/OverspendAlarmZone";
import { RecentTransactionsTable } from "@/components/dashboard/RecentTransactionsTable";
import {
  selectAssetLiabilityRatio,
  selectBudgetUsage,
  selectCashflowSeries,
  selectDTI,
  selectNetCashFlow,
  selectSavingsRate,
  useFinanceStore,
} from "@/lib/store/financeStore";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard · MoneyOS" },
      {
        name: "description",
        content:
          "Cash flow, savings rate, overspend alarms, and asset/liability ratio in one view.",
      },
      { property: "og:title", content: "Dashboard · MoneyOS" },
      {
        property: "og:description",
        content: "High-trust overview of your monthly finances.",
      },
    ],
  }),
  component: DashboardPage,
});

function fmtCurrency(n: number): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function DashboardPage() {
  const state = useFinanceStore();
  const netCashFlow = selectNetCashFlow(state);
  const savingsRate = selectSavingsRate(state);
  const dti = selectDTI(state);
  const alr = selectAssetLiabilityRatio(state);
  const budgetRows = selectBudgetUsage(state);
  const cashflow = selectCashflowSeries(state, 30);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Dashboard
        </h1>
        <p className="text-sm text-muted-foreground">
          Session-scoped snapshot of your finances.
        </p>
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-12">
        <div className="lg:col-span-3">
          <KpiCard
            label="Net cash flow"
            value={fmtCurrency(netCashFlow)}
            tone={netCashFlow >= 0 ? "positive" : "danger"}
            hint="Income minus month-to-date expenses"
          />
        </div>
        <div className="lg:col-span-3">
          <KpiCard
            label="Savings rate"
            value={`${(savingsRate * 100).toFixed(0)}%`}
            tone={savingsRate >= 0.2 ? "positive" : "neutral"}
          />
        </div>
        <div className="lg:col-span-3">
          <KpiCard
            label="Debt-to-income"
            value={`${(dti * 100).toFixed(0)}%`}
            tone={dti > 0.36 ? "danger" : "neutral"}
          />
        </div>
        <div className="lg:col-span-3">
          <KpiCard
            label="Asset / liability"
            value={Number.isFinite(alr) ? alr.toFixed(2) : "∞"}
            tone={alr >= 1 ? "positive" : "neutral"}
          />
        </div>
        <div className="lg:col-span-8">
          <CashflowChart data={cashflow} />
        </div>
        <div className="lg:col-span-4">
          <OverspendAlarmZone rows={budgetRows} />
        </div>
        <div className="lg:col-span-12">
          <RecentTransactionsTable rows={state.transactions} />
        </div>
      </div>
    </div>
  );
}
