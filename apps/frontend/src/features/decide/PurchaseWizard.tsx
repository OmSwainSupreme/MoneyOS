// Feature wrapper for the "Can I buy this?" purchase decision flow.
// Reuses the shared DecisionWizard and the same step schemas/defaults as
// the previous route, but merges `purchaseSeed` so the form opens
// populated. The analyzeDecision server fn already falls back to a
// deterministic verdict when no API key is present — this layer only
// seeds values and marks where a real backend call would slot in.

import { z } from "zod";
import { DecisionWizard, Field, type WizardStep } from "@/components/decide/Wizard";
import { PurchaseDecisionInputSchema, type DecisionInput } from "@/types/finance";
import { purchaseSeed } from "./seeds";

const step1 = z.object({
  itemName: z.string().trim().min(1, "Required").max(120),
  price: z.coerce.number().finite().positive("Must be positive"),
  urgency: z.enum(["now", "3m", "12m"]),
});

const step2 = z
  .object({
    paymentMethod: z.enum(["cash", "credit", "financing"]),
    apr: z.coerce.number().finite().min(0).max(100).optional(),
    termMonths: z.coerce.number().int().min(1).max(600).optional(),
  })
  .superRefine((val, ctx) => {
    if (val.paymentMethod === "financing") {
      if (val.apr === undefined || Number.isNaN(val.apr))
        ctx.addIssue({ code: "custom", path: ["apr"], message: "APR required" });
      if (val.termMonths === undefined || Number.isNaN(val.termMonths))
        ctx.addIssue({ code: "custom", path: ["termMonths"], message: "Term required" });
    }
  });

const step3 = z.object({
  monthlyNetIncome: z.coerce.number().finite().nonnegative(),
  monthlyFixedExpenses: z.coerce.number().finite().nonnegative(),
  liquidSavings: z.coerce.number().finite().nonnegative(),
  emergencyFundMonths: z.coerce.number().finite().min(0).max(60),
});

const steps: WizardStep<z.ZodType>[] = [
  {
    key: "item",
    title: "Item",
    schema: step1,
    defaultValues: {
      itemName: purchaseSeed.itemName ?? "",
      price: purchaseSeed.price ?? 0,
      urgency: purchaseSeed.urgency ?? "3m",
    },
    render: (form) => (
      <>
        <Field
          label="Item name"
          htmlFor="itemName"
          error={form.formState.errors.itemName?.message as string | undefined}
        >
          <input
            id="itemName"
            {...form.register("itemName")}
            aria-invalid={!!form.formState.errors.itemName}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </Field>
        <Field
          label="Price"
          htmlFor="price"
          error={form.formState.errors.price?.message as string | undefined}
        >
          <input
            id="price"
            type="number"
            step="0.01"
            {...form.register("price")}
            aria-invalid={!!form.formState.errors.price}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
          />
        </Field>
        <Field label="Urgency" htmlFor="urgency">
          <select
            id="urgency"
            {...form.register("urgency")}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="now">Now</option>
            <option value="3m">Within 3 months</option>
            <option value="12m">Within 12 months</option>
          </select>
        </Field>
      </>
    ),
  },
  {
    key: "funding",
    title: "Funding",
    schema: step2,
    defaultValues: { paymentMethod: purchaseSeed.paymentMethod ?? "cash" },
    render: (form) => {
      const method = form.watch("paymentMethod");
      return (
        <>
          <Field label="Payment method" htmlFor="paymentMethod">
            <select
              id="paymentMethod"
              {...form.register("paymentMethod")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="cash">Cash</option>
              <option value="credit">Credit card (paid in full)</option>
              <option value="financing">Financing</option>
            </select>
          </Field>
          {method === "financing" ? (
            <>
              <Field
                label="APR (%)"
                htmlFor="apr"
                error={form.formState.errors.apr?.message as string | undefined}
              >
                <input
                  id="apr"
                  type="number"
                  step="0.01"
                  {...form.register("apr")}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
                />
              </Field>
              <Field
                label="Term (months)"
                htmlFor="termMonths"
                error={form.formState.errors.termMonths?.message as string | undefined}
              >
                <input
                  id="termMonths"
                  type="number"
                  step="1"
                  {...form.register("termMonths")}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
                />
              </Field>
            </>
          ) : null}
        </>
      );
    },
  },
  {
    key: "context",
    title: "You",
    schema: step3,
    defaultValues: {
      monthlyNetIncome: purchaseSeed.monthlyNetIncome ?? 0,
      monthlyFixedExpenses: purchaseSeed.monthlyFixedExpenses ?? 0,
      liquidSavings: purchaseSeed.liquidSavings ?? 0,
      emergencyFundMonths: purchaseSeed.emergencyFundMonths ?? 3,
    },
    render: (form) => (
      <>
        {(
          [
            ["monthlyNetIncome", "Monthly net income"],
            ["monthlyFixedExpenses", "Monthly fixed expenses"],
            ["liquidSavings", "Liquid savings"],
            ["emergencyFundMonths", "Emergency fund (months)"],
          ] as const
        ).map(([name, label]) => (
          <Field
            key={name}
            label={label}
            htmlFor={name}
            error={(form.formState.errors[name]?.message as string | undefined) ?? undefined}
          >
            <input
              id={name}
              type="number"
              step="0.01"
              {...form.register(name)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
            />
          </Field>
        ))}
      </>
    ),
  },
];

export function PurchaseWizard({ className }: { className?: string }) {
  const buildInput = (values: Record<string, unknown>): DecisionInput => {
    // TODO(backend): once auth + real model routing land, the
    // DecisionWizard's analyzeDecision call is where a backend verdict
    // (or a different model) would replace the deterministic fallback.
    return PurchaseDecisionInputSchema.parse({ kind: "purchase", ...values });
  };

  return (
    <div className={className}>
      <DecisionWizard
        title="Can I buy this?"
        description="Multi-step check against income, savings, and monthly obligations."
        steps={steps}
        buildInput={buildInput}
      />
    </div>
  );
}
