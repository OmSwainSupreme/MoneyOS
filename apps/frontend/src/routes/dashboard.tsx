import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import {
  BudgetPanel,
  CashflowPanel,
  KpiGrid,
  TransactionsPanel,
  useDashboardData,
} from "@/features/dashboard";

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

function DashboardPage() {
  const { seeded, loadMockData, clearAll } = useDashboardData();

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Dashboard
          </h1>
          <p className="text-sm text-muted-foreground">
            Session-scoped snapshot of your finances.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {!seeded ? (
            <Button onClick={loadMockData} variant="default">
              Load sample data
            </Button>
          ) : (
            <Button onClick={() => clearAll()} variant="outline">
              Clear
            </Button>
          )}
        </div>
      </header>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-12">
        <div className="lg:col-span-12">
          <KpiGrid />
        </div>
        <div className="lg:col-span-8">
          <CashflowPanel />
        </div>
        <div className="lg:col-span-4">
          <BudgetPanel />
        </div>
        <div className="lg:col-span-12">
          <TransactionsPanel />
        </div>
      </div>
    </div>
  );
}
