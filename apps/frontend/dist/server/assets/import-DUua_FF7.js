import { a as TransactionCategorySchema, o as TransactionSchema } from "./finance-BjdKDlHX.js";
import { c as Button, s as useFinanceStore } from "./financeStore-wqInlGKf.js";
import { useCallback, useId, useRef, useState } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { UploadCloud } from "lucide-react";
//#region src/components/import/Dropzone.tsx
var DEFAULT_ACCEPT = [".csv", ".json"];
var DEFAULT_MAX = 5 * 1024 * 1024;
function extensionOf(name) {
	const idx = name.lastIndexOf(".");
	return idx >= 0 ? name.slice(idx).toLowerCase() : "";
}
function Dropzone({ onFile, maxBytes = DEFAULT_MAX, accept = DEFAULT_ACCEPT }) {
	const inputRef = useRef(null);
	const [error, setError] = useState(null);
	const [isOver, setOver] = useState(false);
	const helpId = useId();
	const errorId = useId();
	const handleFile = useCallback((file) => {
		const ext = extensionOf(file.name);
		if (!accept.includes(ext)) {
			setError(`Unsupported file type ${ext || "(unknown)"}. Allowed: ${accept.join(", ")}`);
			return;
		}
		if (file.size > maxBytes) {
			setError(`File too large (${(file.size / 1024 / 1024).toFixed(2)} MB). Max ${(maxBytes / 1024 / 1024).toFixed(0)} MB.`);
			return;
		}
		setError(null);
		onFile(file);
	}, [
		accept,
		maxBytes,
		onFile
	]);
	const open = () => inputRef.current?.click();
	return /* @__PURE__ */ jsxs("div", { children: [
		/* @__PURE__ */ jsxs("div", {
			role: "button",
			tabIndex: 0,
			"aria-label": "Upload a CSV or JSON statement",
			"aria-describedby": `${helpId} ${error ? errorId : ""}`.trim(),
			onClick: open,
			onKeyDown: (e) => {
				if (e.key === "Enter" || e.key === " ") {
					e.preventDefault();
					open();
				}
			},
			onDragOver: (e) => {
				e.preventDefault();
				setOver(true);
			},
			onDragLeave: () => setOver(false),
			onDrop: (e) => {
				e.preventDefault();
				setOver(false);
				const file = e.dataTransfer.files?.[0];
				if (file) handleFile(file);
			},
			className: `flex min-h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed p-6 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring ${isOver ? "border-primary bg-accent" : "border-border bg-card hover:bg-accent"}`,
			children: [
				/* @__PURE__ */ jsx(UploadCloud, {
					"aria-hidden": true,
					className: "h-6 w-6 text-muted-foreground"
				}),
				/* @__PURE__ */ jsx("span", {
					className: "font-medium text-foreground",
					children: "Drop a file or click to browse"
				}),
				/* @__PURE__ */ jsxs("span", {
					id: helpId,
					className: "text-xs text-muted-foreground",
					children: [
						accept.join(", "),
						" · up to ",
						(maxBytes / 1024 / 1024).toFixed(0),
						" MB · parsed in-browser"
					]
				})
			]
		}),
		/* @__PURE__ */ jsx("input", {
			ref: inputRef,
			type: "file",
			accept: accept.join(","),
			className: "sr-only",
			onChange: (e) => {
				const file = e.target.files?.[0];
				if (file) handleFile(file);
				e.target.value = "";
			}
		}),
		error ? /* @__PURE__ */ jsx("p", {
			id: errorId,
			role: "alert",
			className: "mt-2 text-sm text-[color:var(--color-danger-zone)]",
			children: error
		}) : null
	] });
}
//#endregion
//#region src/features/import/sampleStatement.ts
var sampleTransactions = [
	{
		id: "sample-001",
		date: (/* @__PURE__ */ new Date(Date.now() - 20 * 864e5)).toISOString(),
		amount: 4200,
		currency: "USD",
		category: "income",
		merchant: "Acme Corp Payroll",
		source: "import"
	},
	{
		id: "sample-002",
		date: (/* @__PURE__ */ new Date(Date.now() - 18 * 864e5)).toISOString(),
		amount: -1650,
		currency: "USD",
		category: "housing",
		merchant: "Greenfield Apartments",
		source: "import"
	},
	{
		id: "sample-003",
		date: (/* @__PURE__ */ new Date(Date.now() - 12 * 864e5)).toISOString(),
		amount: -320,
		currency: "USD",
		category: "food",
		merchant: "Whole Foods",
		source: "import"
	},
	{
		id: "sample-004",
		date: (/* @__PURE__ */ new Date(Date.now() - 9 * 864e5)).toISOString(),
		amount: -120,
		currency: "USD",
		category: "transport",
		merchant: "Uber",
		source: "import"
	},
	{
		id: "sample-005",
		date: (/* @__PURE__ */ new Date(Date.now() - 6 * 864e5)).toISOString(),
		amount: -140,
		currency: "USD",
		category: "utilities",
		merchant: "City Power",
		source: "import"
	},
	{
		id: "sample-006",
		date: (/* @__PURE__ */ new Date(Date.now() - 4 * 864e5)).toISOString(),
		amount: -80,
		currency: "USD",
		category: "entertainment",
		merchant: "AMC Theatres",
		source: "import"
	},
	{
		id: "sample-007",
		date: (/* @__PURE__ */ new Date(Date.now() - 3 * 864e5)).toISOString(),
		amount: -210,
		currency: "USD",
		category: "shopping",
		merchant: "Apple Store",
		source: "import"
	},
	{
		id: "sample-008",
		date: (/* @__PURE__ */ new Date(Date.now() - 2 * 864e5)).toISOString(),
		amount: -500,
		currency: "USD",
		category: "savings",
		merchant: "Vanguard IRA",
		source: "import"
	}
];
var CSV_HEADER = "id,date,amount,currency,category,merchant,source";
function sampleCsv() {
	return [CSV_HEADER, ...sampleTransactions.map((t) => [
		t.id,
		t.date,
		t.amount,
		t.currency,
		t.category,
		`"${t.merchant.replace(/"/g, "\"\"")}"`,
		t.source
	].join(","))].join("\n");
}
function sampleJson() {
	return JSON.stringify(sampleTransactions, null, 2);
}
function downloadSample(kind) {
	const isCsv = kind === "csv";
	const content = isCsv ? sampleCsv() : sampleJson();
	const blob = new Blob([content], { type: `${isCsv ? "text/csv" : "application/json"};charset=utf-8` });
	const url = URL.createObjectURL(blob);
	const anchor = document.createElement("a");
	anchor.href = url;
	anchor.download = `sample-transactions.${kind}`;
	document.body.appendChild(anchor);
	anchor.click();
	anchor.remove();
	URL.revokeObjectURL(url);
}
//#endregion
//#region src/features/import/useSampleData.ts
function useSampleData() {
	const addTransactions = useFinanceStore((s) => s.addTransactions);
	const loadSample = () => {
		addTransactions(sampleTransactions);
	};
	return {
		loadSample,
		downloadSample
	};
}
//#endregion
//#region src/routes/import.tsx?tsr-split=component
var CATEGORY_VALUES = TransactionCategorySchema.options;
function coerceCategory(input) {
	const v = String(input ?? "").toLowerCase();
	return CATEGORY_VALUES.includes(v) ? v : "other";
}
function normalizeRow(raw, index) {
	const lower = {};
	for (const [k, v] of Object.entries(raw)) lower[k.toLowerCase()] = v;
	const dateRaw = lower.date ?? lower.posted ?? lower.timestamp;
	const parsedDate = dateRaw ? new Date(String(dateRaw)) : null;
	const iso = parsedDate && !Number.isNaN(parsedDate.getTime()) ? parsedDate.toISOString() : "";
	const amountRaw = lower.amount ?? lower.value ?? lower.net;
	const amount = typeof amountRaw === "number" ? amountRaw : Number(amountRaw);
	return {
		id: String(lower.id ?? `row-${index}-${crypto.randomUUID()}`),
		date: iso,
		amount,
		currency: String(lower.currency ?? "USD").toUpperCase(),
		category: coerceCategory(lower.category),
		merchant: String(lower.merchant ?? lower.description ?? lower.memo ?? ""),
		source: "import",
		rawDescription: lower.description !== void 0 ? String(lower.description) : void 0
	};
}
function ImportPage() {
	const addTransactions = useFinanceStore((s) => s.addTransactions);
	const { loadSample } = useSampleData();
	const [rows, setRows] = useState([]);
	const [busy, setBusy] = useState(false);
	const [notice, setNotice] = useState(null);
	const validate = (records) => records.map((raw, index) => {
		const normalized = normalizeRow(raw, index);
		const parsed = TransactionSchema.safeParse(normalized);
		if (parsed.success) return {
			index,
			raw,
			valid: true,
			data: parsed.data
		};
		const first = parsed.error.issues[0];
		return {
			index,
			raw,
			valid: false,
			error: `${first.path.join(".") || "row"}: ${first.message}`
		};
	});
	const handleFile = async (file) => {
		setBusy(true);
		setNotice(null);
		setRows([]);
		try {
			const text = await file.text();
			const ext = file.name.toLowerCase().endsWith(".json") ? "json" : "csv";
			let records = [];
			if (ext === "json") {
				const parsed = JSON.parse(text);
				if (!Array.isArray(parsed)) throw new Error("JSON root must be an array of transaction objects.");
				records = parsed;
			} else records = (await import("papaparse")).default.parse(text, {
				header: true,
				skipEmptyLines: true,
				dynamicTyping: true
			}).data;
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
		const data = validRows.map((r) => r.data);
		addTransactions(data);
		setNotice(`Merged ${data.length} transaction${data.length === 1 ? "" : "s"}.`);
		setRows([]);
	};
	return /* @__PURE__ */ jsxs("div", {
		className: "mx-auto max-w-4xl px-4 py-8 sm:px-6",
		children: [
			/* @__PURE__ */ jsxs("header", {
				className: "mb-6 flex flex-wrap items-start justify-between gap-3",
				children: [/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("h1", {
					className: "text-2xl font-semibold tracking-tight text-foreground",
					children: "Import statement"
				}), /* @__PURE__ */ jsx("p", {
					className: "text-sm text-muted-foreground",
					children: "Files stay in your browser. Nothing is uploaded."
				})] }), /* @__PURE__ */ jsxs("div", {
					className: "flex flex-wrap gap-2",
					children: [
						/* @__PURE__ */ jsx(Button, {
							onClick: loadSample,
							variant: "outline",
							children: "Load sample data"
						}),
						/* @__PURE__ */ jsx(Button, {
							onClick: () => downloadSample("csv"),
							variant: "ghost",
							children: "Download CSV"
						}),
						/* @__PURE__ */ jsx(Button, {
							onClick: () => downloadSample("json"),
							variant: "ghost",
							children: "Download JSON"
						})
					]
				})]
			}),
			/* @__PURE__ */ jsx(Dropzone, { onFile: handleFile }),
			busy ? /* @__PURE__ */ jsx("p", {
				role: "status",
				className: "mt-4 text-sm text-muted-foreground",
				children: "Parsing…"
			}) : null,
			notice ? /* @__PURE__ */ jsx("p", {
				role: "status",
				className: "mt-4 text-sm text-foreground",
				children: notice
			}) : null,
			rows.length > 0 ? /* @__PURE__ */ jsxs("section", {
				className: "mt-6 rounded-md border border-border bg-card p-4",
				children: [/* @__PURE__ */ jsxs("div", {
					className: "flex flex-wrap items-center justify-between gap-3",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "text-sm text-muted-foreground",
						children: [
							rows.length,
							" rows parsed · ",
							validRows.length,
							" valid ·",
							" ",
							rows.length - validRows.length,
							" invalid"
						]
					}), /* @__PURE__ */ jsxs("button", {
						type: "button",
						onClick: merge,
						disabled: validRows.length === 0,
						className: "inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50",
						children: [
							"Merge ",
							validRows.length,
							" valid"
						]
					})]
				}), /* @__PURE__ */ jsx("div", {
					className: "mt-3 max-h-96 overflow-auto",
					children: /* @__PURE__ */ jsxs("table", {
						className: "w-full text-sm",
						children: [/* @__PURE__ */ jsx("thead", { children: /* @__PURE__ */ jsxs("tr", {
							className: "border-b border-border text-left text-muted-foreground",
							children: [
								/* @__PURE__ */ jsx("th", {
									scope: "col",
									className: "py-2 pr-2",
									children: "#"
								}),
								/* @__PURE__ */ jsx("th", {
									scope: "col",
									className: "py-2 pr-2",
									children: "Status"
								}),
								/* @__PURE__ */ jsx("th", {
									scope: "col",
									className: "py-2 pr-2",
									children: "Date"
								}),
								/* @__PURE__ */ jsx("th", {
									scope: "col",
									className: "py-2 pr-2",
									children: "Merchant"
								}),
								/* @__PURE__ */ jsx("th", {
									scope: "col",
									className: "py-2 pr-2 text-right",
									children: "Amount"
								}),
								/* @__PURE__ */ jsx("th", {
									scope: "col",
									className: "py-2 pr-2",
									children: "Notes"
								})
							]
						}) }), /* @__PURE__ */ jsx("tbody", { children: rows.map((r) => /* @__PURE__ */ jsxs("tr", {
							className: "border-b border-border last:border-0",
							children: [
								/* @__PURE__ */ jsx("td", {
									className: "py-2 pr-2 tabular-nums text-muted-foreground",
									children: r.index + 1
								}),
								/* @__PURE__ */ jsx("td", {
									className: "py-2 pr-2",
									children: /* @__PURE__ */ jsx("span", {
										className: `inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${r.valid ? "bg-[color:var(--color-positive)]/15 text-[color:var(--color-positive)]" : "bg-[color:var(--color-danger-zone)]/15 text-[color:var(--color-danger-zone)]"}`,
										children: r.valid ? "OK" : "Invalid"
									})
								}),
								/* @__PURE__ */ jsx("td", {
									className: "py-2 pr-2 tabular-nums text-muted-foreground",
									children: r.data?.date?.slice(0, 10) ?? String(r.raw.date ?? "")
								}),
								/* @__PURE__ */ jsx("td", {
									className: "py-2 pr-2 text-foreground",
									children: r.data?.merchant ?? String(r.raw.merchant ?? r.raw.description ?? "")
								}),
								/* @__PURE__ */ jsx("td", {
									className: "py-2 pr-2 text-right tabular-nums text-foreground",
									children: r.data ? r.data.amount.toFixed(2) : String(r.raw.amount ?? "")
								}),
								/* @__PURE__ */ jsx("td", {
									className: "py-2 pr-2 text-xs text-muted-foreground",
									children: r.error ?? ""
								})
							]
						}, r.index)) })]
					})
				})]
			}) : null
		]
	});
}
//#endregion
export { ImportPage as component };
