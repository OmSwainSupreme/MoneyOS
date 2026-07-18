import { OverspendAlarmZone } from "@/components/dashboard/OverspendAlarmZone";
import {
  selectBudgetUsage,
  useFinanceStore,
} from "@/lib/store/financeStore";

// Overspend alarms per budget category, derived from the finance store.
export function BudgetPanel({ className }: { className?: string }) {
  const state = useFinanceStore();
  const rows = selectBudgetUsage(state);
  return (
    <div className={className}>
      <OverspendAlarmZone rows={rows} />
    </div>
  );
}
