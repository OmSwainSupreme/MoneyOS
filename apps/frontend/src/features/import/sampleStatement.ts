// Canned sample statement generator for the import flow. Produces both a
// CSV string and a JSON array matching the TransactionSchema shape that
// the import route's normalizeRow/validate pipeline expects.

import type { Transaction } from "@/types/finance";

// Hand-built rows within the last ~30 days so they land in current-month
// selectors. Categories mirror the TransactionCategory enum.
export const sampleTransactions: Transaction[] = [
  {
    id: "sample-001",
    date: new Date(Date.now() - 20 * 864e5).toISOString(),
    amount: 4200,
    currency: "USD",
    category: "income",
    merchant: "Acme Corp Payroll",
    source: "import",
  },
  {
    id: "sample-002",
    date: new Date(Date.now() - 18 * 864e5).toISOString(),
    amount: -1650,
    currency: "USD",
    category: "housing",
    merchant: "Greenfield Apartments",
    source: "import",
  },
  {
    id: "sample-003",
    date: new Date(Date.now() - 12 * 864e5).toISOString(),
    amount: -320,
    currency: "USD",
    category: "food",
    merchant: "Whole Foods",
    source: "import",
  },
  {
    id: "sample-004",
    date: new Date(Date.now() - 9 * 864e5).toISOString(),
    amount: -120,
    currency: "USD",
    category: "transport",
    merchant: "Uber",
    source: "import",
  },
  {
    id: "sample-005",
    date: new Date(Date.now() - 6 * 864e5).toISOString(),
    amount: -140,
    currency: "USD",
    category: "utilities",
    merchant: "City Power",
    source: "import",
  },
  {
    id: "sample-006",
    date: new Date(Date.now() - 4 * 864e5).toISOString(),
    amount: -80,
    currency: "USD",
    category: "entertainment",
    merchant: "AMC Theatres",
    source: "import",
  },
  {
    id: "sample-007",
    date: new Date(Date.now() - 3 * 864e5).toISOString(),
    amount: -210,
    currency: "USD",
    category: "shopping",
    merchant: "Apple Store",
    source: "import",
  },
  {
    id: "sample-008",
    date: new Date(Date.now() - 2 * 864e5).toISOString(),
    amount: -500,
    currency: "USD",
    category: "savings",
    merchant: "Vanguard IRA",
    source: "import",
  },
];

const CSV_HEADER = "id,date,amount,currency,category,merchant,source";

export function sampleCsv(): string {
  const rows = sampleTransactions.map((t) =>
    [
      t.id,
      t.date,
      t.amount,
      t.currency,
      t.category,
      `"${t.merchant.replace(/"/g, '""')}"`,
      t.source,
    ].join(","),
  );
  return [CSV_HEADER, ...rows].join("\n");
}

export function sampleJson(): string {
  return JSON.stringify(sampleTransactions, null, 2);
}

export function downloadSample(kind: "csv" | "json"): void {
  // TODO(backend): fetch the real import template from
  // `/api/import/template` instead of using this canned sample.
  const isCsv = kind === "csv";
  const content = isCsv ? sampleCsv() : sampleJson();
  const mime = isCsv ? "text/csv" : "application/json";
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `sample-transactions.${kind}`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
