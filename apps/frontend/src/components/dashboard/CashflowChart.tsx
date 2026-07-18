import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CashflowPoint } from "@/lib/store/financeStore";

export function CashflowChart({ data }: { data: CashflowPoint[] }) {
  const summary =
    data.length === 0
      ? "No transactions in the last 30 days."
      : `Daily net cash flow across ${data.length} days, ranging from ${Math.min(...data.map((d) => d.net)).toFixed(2)} to ${Math.max(...data.map((d) => d.net)).toFixed(2)}.`;

  return (
    <div className="rounded-md border border-border bg-card p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-card-foreground">
          Cash flow (30 days)
        </h2>
        <span className="text-xs text-muted-foreground">Daily net</span>
      </div>
      <div
        className="mt-3 h-56 w-full"
        role="img"
        aria-label={summary}
      >
        {data.length === 0 ? (
          <EmptyState />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="cashflowFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-positive)" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="var(--color-positive)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              />
              <YAxis tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }} />
              <Tooltip
                contentStyle={{
                  background: "var(--color-popover)",
                  color: "var(--color-popover-foreground)",
                  border: "1px solid var(--color-border)",
                  borderRadius: 6,
                  fontSize: 12,
                }}
              />
              <Area
                type="monotone"
                dataKey="net"
                stroke="var(--color-positive)"
                strokeWidth={2}
                fill="url(#cashflowFill)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
      <table className="sr-only">
        <caption>Daily net cash flow, last 30 days</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Net</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d) => (
            <tr key={d.date}>
              <td>{d.date}</td>
              <td>{d.net.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      Import a statement to populate this chart.
    </div>
  );
}
