import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { DecisionWizard, Field, type WizardStep } from "@/components/decide/Wizard";
import { LoanDecisionInputSchema, type DecisionInput } from "@/types/finance";

export const Route = createFileRoute("/decide/loan")({
  head: () => ({
    meta: [
      { title: "Should I take this loan? · MoneyOS" },
      {
        name: "description",
        content:
          "Estimate monthly payment, total interest, and post-loan DTI before signing.",
      },
      { property: "og:title", content: "Should I take this loan? · MoneyOS" },
      {
        property: "og:description",
        content: "Multi-step loan stress test with structured AI verdict.",
      },
    ],
  }),
  component: LoanPage,
});

const stepLoan = z.object({
  principal: z.coerce.number().finite().positive(),
  apr: z.coerce.number().finite().min(0).max(100),
  termMonths: z.coerce.number().int().min(1).max(600),
  purpose: z.string().trim().min(1).max(200),
});

const stepBudget = z.object({
  existingMonthlyDebt: z.coerce.number().finite().nonnegative(),
  monthlyNetIncome: z.coerce.number().finite().nonnegative(),
  liquidSavings: z.coerce.number().finite().nonnegative(),
});

function LoanPage() {
  const steps: WizardStep<z.ZodType>[] = [
    {
      key: "loan",
      title: "Loan",
      schema: stepLoan,
      defaultValues: { principal: 0, apr: 0, termMonths: 12, purpose: "" },
      render: (form) => (
        <>
          <Field label="Principal" htmlFor="principal" error={form.formState.errors.principal?.message as string | undefined}>
            <input
              id="principal"
              type="number"
              step="0.01"
              {...form.register("principal")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
            />
          </Field>
          <Field label="APR (%)" htmlFor="apr" error={form.formState.errors.apr?.message as string | undefined}>
            <input
              id="apr"
              type="number"
              step="0.01"
              {...form.register("apr")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
            />
          </Field>
          <Field label="Term (months)" htmlFor="termMonths" error={form.formState.errors.termMonths?.message as string | undefined}>
            <input
              id="termMonths"
              type="number"
              step="1"
              {...form.register("termMonths")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
            />
          </Field>
          <Field label="Purpose" htmlFor="purpose" error={form.formState.errors.purpose?.message as string | undefined}>
            <input
              id="purpose"
              {...form.register("purpose")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </Field>
        </>
      ),
    },
    {
      key: "budget",
      title: "Budget",
      schema: stepBudget,
      defaultValues: {
        existingMonthlyDebt: 0,
        monthlyNetIncome: 0,
        liquidSavings: 0,
      },
      render: (form) => (
        <>
          {(
            [
              ["existingMonthlyDebt", "Existing monthly debt payments"],
              ["monthlyNetIncome", "Monthly net income"],
              ["liquidSavings", "Liquid savings"],
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
    LoanDecisionInputSchema.parse({ kind: "loan", ...values });

  return (
    <DecisionWizard
      title="Should I take this loan?"
      description="Two-step check for monthly impact, DTI, and runway."
      steps={steps}
      buildInput={buildInput}
    />
  );
}
