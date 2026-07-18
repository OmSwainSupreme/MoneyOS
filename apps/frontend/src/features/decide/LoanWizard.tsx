// Feature wrapper for the "Should I take this loan?" loan decision flow.
// Reuses the shared DecisionWizard and the same step schemas/defaults as
// the previous route, but merges `loanSeed` so the form opens populated.
// The analyzeDecision server fn already falls back to a deterministic
// verdict when no API key is present — this layer only seeds values
// and marks where a real backend call would slot in.

import { z } from "zod";
import { DecisionWizard, Field, type WizardStep } from "@/components/decide/Wizard";
import { LoanDecisionInputSchema, type DecisionInput } from "@/types/finance";
import { loanSeed } from "./seeds";

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

const steps: WizardStep<z.ZodType>[] = [
  {
    key: "loan",
    title: "Loan",
    schema: stepLoan,
    defaultValues: {
      principal: loanSeed.principal ?? 0,
      apr: loanSeed.apr ?? 0,
      termMonths: loanSeed.termMonths ?? 12,
      purpose: loanSeed.purpose ?? "",
    },
    render: (form) => (
      <>
        <Field
          label="Principal"
          htmlFor="principal"
          error={form.formState.errors.principal?.message as string | undefined}
        >
          <input
            id="principal"
            type="number"
            step="0.01"
            {...form.register("principal")}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm tabular-nums"
          />
        </Field>
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
        <Field
          label="Purpose"
          htmlFor="purpose"
          error={form.formState.errors.purpose?.message as string | undefined}
        >
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
      existingMonthlyDebt: loanSeed.existingMonthlyDebt ?? 0,
      monthlyNetIncome: loanSeed.monthlyNetIncome ?? 0,
      liquidSavings: loanSeed.liquidSavings ?? 0,
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

export function LoanWizard({ className }: { className?: string }) {
  const buildInput = (values: Record<string, unknown>): DecisionInput => {
    // TODO(backend): once auth + real model routing land, the
    // DecisionWizard's analyzeDecision call is where a backend verdict
    // (or a different model) would replace the deterministic fallback.
    return LoanDecisionInputSchema.parse({ kind: "loan", ...values });
  };

  return (
    <div className={className}>
      <DecisionWizard
        title="Should I take this loan?"
        description="Two-step check for monthly impact, DTI, and runway."
        steps={steps}
        buildInput={buildInput}
      />
    </div>
  );
}
