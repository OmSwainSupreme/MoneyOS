import { RecentTransactionsTable } from "@/components/dashboard/RecentTransactionsTable";
import { useFinanceStore } from "@/lib/store/financeStore";

// Recent transactions table reading from the finance store.
export function TransactionsPanel({ className }: { className?: string }) {
  const state = useFinanceStore();
  return (
    <div className={className}>
      <RecentTransactionsTable rows={state.transactions} />
    </div>
  );
}
