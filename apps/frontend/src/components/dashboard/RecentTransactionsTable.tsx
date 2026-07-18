import type { Transaction } from "@/types/finance";

export function RecentTransactionsTable({ rows }: { rows: Transaction[] }) {
  const latest = [...rows]
    .sort((a, b) => (a.date < b.date ? 1 : -1))
    .slice(0, 20);

  return (
    <div className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-semibold text-card-foreground">
        Recent transactions
      </h2>
      {latest.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">
          Import a statement to see transactions here.
        </p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th scope="col" className="py-2 pr-2 font-medium">
                  Date
                </th>
                <th scope="col" className="py-2 pr-2 font-medium">
                  Merchant
                </th>
                <th scope="col" className="py-2 pr-2 font-medium">
                  Category
                </th>
                <th scope="col" className="py-2 text-right font-medium">
                  Amount
                </th>
              </tr>
            </thead>
            <tbody>
              {latest.map((t) => (
                <tr key={t.id} className="border-b border-border last:border-0">
                  <td className="py-2 pr-2 text-muted-foreground tabular-nums">
                    {t.date.slice(0, 10)}
                  </td>
                  <td className="py-2 pr-2 text-foreground">{t.merchant || "—"}</td>
                  <td className="py-2 pr-2 capitalize text-muted-foreground">
                    {t.category}
                  </td>
                  <td
                    className={`py-2 text-right tabular-nums ${
                      t.amount < 0
                        ? "text-[color:var(--color-danger-zone)]"
                        : "text-[color:var(--color-positive)]"
                    }`}
                  >
                    {t.amount.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
