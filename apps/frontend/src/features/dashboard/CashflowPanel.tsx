import { CashflowChart } from "@/components/dashboard/CashflowChart";
import {
  selectCashflowSeries,
  useFinanceStore,
} from "@/lib/store/financeStore";

// 30-day net cash-flow chart reading from the finance store.
export function CashflowPanel({
  days = 30,
  className,
}: {
  days?: number;
  className?: string;
}) {
  const state = useFinanceStore();
  const data = selectCashflowSeries(state, days);
  return (
    <div className={className}>
      <CashflowChart data={data} />
    </div>
  );
}
