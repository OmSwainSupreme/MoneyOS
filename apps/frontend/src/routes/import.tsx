import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dropzone } from "@/components/import/Dropzone";
import { useFinanceStore } from "@/lib/store/financeStore";
import {
  downloadSample,
  useSampleData,
} from "@/features/import";
import {
  TransactionCategorySchema,
  TransactionSchema,
  type Transaction,
  type TransactionCategory,
} from "@/types/finance";

export const Route = createFileRoute("/import")({
  head: () => ({
    meta: [
      { title: "Import statement · MoneyOS" },
      {
        name: "description",
        content: "Sandboxed in-browser CSV or JSON parsing with row-level validation.",
      },
      { property: "og:title", content: "Import statement · MoneyOS" },
      {
        property: "og:description",
        content: "Parse and validate your statements before anything is stored.",
      },
    ],
  }),
  component: ImportPage,
});

interface RowResult {
  index: number;
  raw: Record<string, unknown>;
  valid: boolean;
  data?: Transaction;
  error?: string;
}

const CATEGORY_VALUES: readonly TransactionCategory[] =
  TransactionCategorySchema.options;

function coerceCategory(input: unknown): TransactionCategory {
  const v = String(input ?? "").toLowerCase();
  return (CATEGORY_VALUES as readonly string[]).includes(v)
    ? (v as TransactionCategory)
    : "other";
}

function normalizeRow(raw: Record<string, unknown>, index: number): unknown {
  const lower: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(raw)) lower[k.toLowerCase()] = v;
  const dateRaw = lower.date ?? lower.posted ?? lower.timestamp;
  const parsedDate = dateRaw ? new Date(String(dateRaw)) : null;
  const iso =
    parsedDate && !Number.isNaN(parsedDate.getTime())
      ? parsedDate.toISOString()
      : "";
  const amountRaw = lower.amount ?? lower.value ?? lower.net;
  const amount = typeof amountRaw === "number" ? amountRaw : Number(amountRaw);
  return {
    id: String(lower.id ?? `row-${index}-${crypto.randomUUID()}`),
    date: iso,
    amount,
    currency: String(lower.currency ?? "USD").toUpperCase(),
    category: coerceCategory(lower.category),
    merchant: String(lower.merchant ?? lower.description ?? lower.memo ?? ""),
    source: "import" as const,
    rawDescription:
      lower.description !== undefined ? String(lower.description) : undefined,
  };
}

function ImportPage() {
  const addTransactions = useFinanceStore((s) => s.addTransactions);
  const { loadSample } = useSampleData();
  const [rows, setRows] = useState<RowResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const validate = (records: Record<string, unknown>[]): RowResult[] =>
    records.map((raw, index) => {
      const normalized = normalizeRow(raw, index);
      const parsed = TransactionSchema.safeParse(normalized);
      if (parsed.success) {
        return { index, raw, valid: true, data: parsed.data };
      }
      const first = parsed.error.issues[0];
      return {
        index,
        raw,
        valid: false,
        error: `${first.path.join(".") || "row"}: ${first.message}`,
      };
    });

  const handleFile = async (file: File) => {
    setBusy(true);
    setNotice(null);
    setRows([]);
    try {
      const text = await file.text();
      const ext = file.name.toLowerCase().endsWith(".json") ? "json" : "csv";
      let records: Record<string, unknown>[] = [];
      if (ext === "json") {
        const parsed = JSON.parse(text) as unknown;
        if (!Array.isArray(parsed)) {
          throw new Error("JSON root must be an array of transaction objects.");
        }
        records = parsed as Record<string, unknown>[];
      } else {
        const Papa = (await import("papaparse")).default;
        const result = Papa.parse<Record<string, unknown>>(text, {
          header: true,
          skipEmptyLines: true,
          dynamicTyping: true,
        });
        records = result.data;
      }
      setRows(validate(records));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to parse file.";
      setNotice(msg);
    } finally {
      setBusy(false);
    }
  };

  const validRows = rows.filter((r) => r.valid && r.data);

  const merge = () => {
    const data: Transaction[] = validRows.map((r) => r.data!);
    addTransactions(data);
    setNotice(`Merged ${data.length} transaction${data.length === 1 ? "" : "s"}.`);
    setRows([]);
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Import statement
          </h1>
          <p className="text-sm text-muted-foreground">
            Files stay in your browser. Nothing is uploaded.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {/* TODO(backend): replace client-only sample merge with a server
              upload + reconcile once the import API exists. */}
          <Button onClick={loadSample} variant="outline">
            Load sample data
          </Button>
          <Button
            onClick={() => downloadSample("csv")}
            variant="ghost"
          >
            Download CSV
          </Button>
          <Button
            onClick={() => downloadSample("json")}
            variant="ghost"
          >
            Download JSON
          </Button>
        </div>
      </header>
      <Dropzone onFile={handleFile} />
      {busy ? (
        <p role="status" className="mt-4 text-sm text-muted-foreground">
          Parsing…
        </p>
      ) : null}
      {notice ? (
        <p role="status" className="mt-4 text-sm text-foreground">
          {notice}
        </p>
      ) : null}
      {rows.length > 0 ? (
        <section className="mt-6 rounded-md border border-border bg-card p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-muted-foreground">
              {rows.length} rows parsed · {validRows.length} valid ·{" "}
              {rows.length - validRows.length} invalid
            </div>
            <button
              type="button"
              onClick={merge}
              disabled={validRows.length === 0}
              className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              Merge {validRows.length} valid
            </button>
          </div>
          <div className="mt-3 max-h-96 overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th scope="col" className="py-2 pr-2">
                    #
                  </th>
                  <th scope="col" className="py-2 pr-2">
                    Status
                  </th>
                  <th scope="col" className="py-2 pr-2">
                    Date
                  </th>
                  <th scope="col" className="py-2 pr-2">
                    Merchant
                  </th>
                  <th scope="col" className="py-2 pr-2 text-right">
                    Amount
                  </th>
                  <th scope="col" className="py-2 pr-2">
                    Notes
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.index} className="border-b border-border last:border-0">
                    <td className="py-2 pr-2 tabular-nums text-muted-foreground">
                      {r.index + 1}
                    </td>
                    <td className="py-2 pr-2">
                      <span
                        className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${
                          r.valid
                            ? "bg-[color:var(--color-positive)]/15 text-[color:var(--color-positive)]"
                            : "bg-[color:var(--color-danger-zone)]/15 text-[color:var(--color-danger-zone)]"
                        }`}
                      >
                        {r.valid ? "OK" : "Invalid"}
                      </span>
                    </td>
                    <td className="py-2 pr-2 tabular-nums text-muted-foreground">
                      {r.data?.date?.slice(0, 10) ?? String(r.raw.date ?? "")}
                    </td>
                    <td className="py-2 pr-2 text-foreground">
                      {r.data?.merchant ?? String(r.raw.merchant ?? r.raw.description ?? "")}
                    </td>
                    <td className="py-2 pr-2 text-right tabular-nums text-foreground">
                      {r.data ? r.data.amount.toFixed(2) : String(r.raw.amount ?? "")}
                    </td>
                    <td className="py-2 pr-2 text-xs text-muted-foreground">
                      {r.error ?? ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
