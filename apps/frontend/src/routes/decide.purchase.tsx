import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { DecisionWizard, Field, type WizardStep } from "@/components/decide/Wizard";
import { PurchaseDecisionInputSchema, type DecisionInput } from "@/types/finance";

export const Route = createFileRoute("/decide/purchase")({
  head: () => ({
    meta: [
      { title: "Can I buy this? · MoneyOS" },
      {
        name: "description",
        content: "Stress-test a purchase against your income, savings, and monthly obligations.",
      },
      { property: "og:title", content: "Can I buy this? · MoneyOS" },
      {
        property: "og:description",
        content: "Structured multi-step check before you commit to a purchase.",
      },
    ],
  }),
  component: PurchasePage,
});

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

function PurchasePage() {
  const steps: WizardStep<z.ZodType>[] = [
    {
      key: "item",
      title: "Item",
      schema: step1,
      defaultValues: { itemName: "", price: 0, urgency: "3m" },
      render: (form) => (
        <>
          <Field label="Item name" htmlFor="itemName" error={form.formState.errors.itemName?.message as string | undefined}>
            <input
              id="itemName"
              {...form.register("itemName")}
              aria-invalid={!!form.formState.errors.itemName}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Price" htmlFor="price" error={form.formState.errors.price?.message as string | undefined}>
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
      defaultValues: { paymentMethod: "cash" },
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
                <Field label="APR (%)" htmlFor="apr" error={form.formState.errors.apr?.message as string | undefined}>
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
        monthlyNetIncome: 0,
        monthlyFixedExpenses: 0,
        liquidSavings: 0,
        emergencyFundMonths: 3,
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

  const buildInput = (values: Record<string, unknown>): DecisionInput =>
    PurchaseDecisionInputSchema.parse({ kind: "purchase", ...values });

  return (
    <DecisionWizard
      title="Can I buy this?"
      description="Multi-step check against income, savings, and monthly obligations."
      steps={steps}
      buildInput={buildInput}
    />
  );
}
