import { AlertTriangle } from "lucide-react";
import type { BudgetUsageRow } from "@/lib/store/financeStore";

export function OverspendAlarmZone({ rows }: { rows: BudgetUsageRow[] }) {
  const overspent = rows.filter((r) => r.pct >= 1);

  return (
    <div className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-semibold text-card-foreground">Overspend alarms</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">
          No budgets defined yet. Add category limits to enable overspend detection.
        </p>
      ) : (
        <>
          <ul aria-live="polite" className="mt-3 space-y-2">
            {rows.map((row) => {
              const over = row.pct >= 1;
              const pctText = `${(row.pct * 100).toFixed(0)}%`;
              return (
                <li key={row.category} className="text-sm">
                  <div className="flex items-center justify-between">
                    <span className="capitalize text-foreground">{row.category}</span>
                    <span className="tabular-nums text-muted-foreground">
                      {row.spent.toFixed(2)} / {row.limit.toFixed(2)} · {pctText}
                    </span>
                  </div>
                  <div
                    className="mt-1 h-2 w-full overflow-hidden rounded-md bg-muted"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.min(100, Math.round(row.pct * 100))}
                    aria-label={`${row.category} budget usage`}
                  >
                    <div
                      className="h-full"
                      style={{
                        width: `${Math.min(100, row.pct * 100).toFixed(1)}%`,
                        backgroundColor: over
                          ? "var(--color-danger-zone)"
                          : "var(--color-positive)",
                      }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
          {overspent.length > 0 ? (
            <div
              role="alert"
              className="mt-3 flex items-start gap-2 rounded-md border border-[color:var(--color-danger-zone)]/40 bg-[color:var(--color-danger-zone)]/10 p-2 text-sm text-[color:var(--color-danger-zone)]"
            >
              <AlertTriangle aria-hidden className="mt-0.5 h-4 w-4" />
              <span>
                {overspent.length} categor{overspent.length === 1 ? "y is" : "ies are"}{" "}
                over budget this month.
              </span>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
