import { zodResolver } from "@hookform/resolvers/zod";
import { useServerFn } from "@tanstack/react-start";
import { useState } from "react";
import { useForm, type UseFormReturn } from "react-hook-form";
import type { z, ZodType } from "zod";
import { analyzeDecision } from "@/lib/decision.functions";
import type { DecisionInput, DecisionVerdict } from "@/types/finance";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface WizardStep<TSchema extends ZodType = ZodType<any>> {
  key: string;
  title: string;
  schema: TSchema;
  defaultValues: z.infer<TSchema>;
  render: (form: UseFormReturn<z.infer<TSchema>>) => React.ReactNode;
}

export interface WizardProps {
  title: string;
  description: string;
  buildInput: (values: Record<string, unknown>) => DecisionInput;
  steps: WizardStep[];
}

export function DecisionWizard({ title, description, steps, buildInput }: WizardProps) {
  const [current, setCurrent] = useState(0);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [verdict, setVerdict] = useState<DecisionVerdict | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const analyze = useServerFn(analyzeDecision);

  const step = steps[current];
  const isLast = current === steps.length - 1;

  const handleStepSubmit = async (stepValues: Record<string, unknown>) => {
    const merged = { ...values, ...stepValues };
    setValues(merged);
    if (!isLast) {
      setCurrent((c) => c + 1);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const input = buildInput(merged);
      const result = await analyze({ data: input });
      setVerdict(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setSubmitting(false);
    }
  };

  if (verdict) {
    const tone =
      verdict.verdict === "yes"
        ? "text-[color:var(--color-positive)]"
        : verdict.verdict === "no"
          ? "text-[color:var(--color-danger-zone)]"
          : "text-foreground";
    return (
      <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        <div className="mt-6 rounded-md border border-border bg-card p-6">
          <div className={`text-xs font-medium uppercase tracking-wide ${tone}`}>
            Verdict: {verdict.verdict}
          </div>
          <h2 className={`mt-2 text-xl font-semibold ${tone}`}>{verdict.headline}</h2>
          <p className="mt-3 text-sm text-foreground">{verdict.rationale}</p>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Monthly impact</dt>
              <dd className="tabular-nums text-foreground">
                {verdict.monthlyImpact.toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Savings runway</dt>
              <dd className="tabular-nums text-foreground">
                {verdict.savingsRunwayMonths.toFixed(1)} months
              </dd>
            </div>
          </dl>
          <button
            type="button"
            onClick={() => {
              setVerdict(null);
              setValues({});
              setCurrent(0);
            }}
            className="mt-6 inline-flex min-h-11 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground hover:bg-accent"
          >
            Start over
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </header>
      <ol className="mb-4 flex items-center gap-3 text-xs text-muted-foreground" aria-label="Progress">
        {steps.map((s, i) => (
          <li key={s.key} className="flex items-center gap-2">
            <span
              className={`inline-flex h-6 w-6 items-center justify-center rounded-md tabular-nums ${
                i === current
                  ? "bg-primary text-primary-foreground"
                  : i < current
                    ? "bg-accent text-accent-foreground"
                    : "border border-border"
              }`}
              aria-current={i === current ? "step" : undefined}
            >
              {i + 1}
            </span>
            <span className={i === current ? "font-medium text-foreground" : ""}>
              {s.title}
            </span>
          </li>
        ))}
      </ol>
      <StepForm
        key={step.key}
        step={step}
        initialValues={values}
        canGoBack={current > 0}
        isLast={isLast}
        submitting={submitting}
        error={error}
        onBack={() => setCurrent((c) => Math.max(0, c - 1))}
        onSubmit={handleStepSubmit}
      />
    </div>
  );
}

interface StepFormProps {
  step: WizardStep;
  initialValues: Record<string, unknown>;
  canGoBack: boolean;
  isLast: boolean;
  submitting: boolean;
  error: string | null;
  onBack: () => void;
  onSubmit: (values: Record<string, unknown>) => void | Promise<void>;
}

function StepForm({
  step,
  initialValues,
  canGoBack,
  isLast,
  submitting,
  error,
  onBack,
  onSubmit,
}: StepFormProps) {
  const form = useForm({
    resolver: zodResolver(step.schema),
    defaultValues: { ...step.defaultValues, ...initialValues } as never,
    mode: "onChange",
  });

  const handle = form.handleSubmit(async (v) => {
    await onSubmit(v as Record<string, unknown>);
  });

  return (
    <form onSubmit={handle} noValidate className="rounded-md border border-border bg-card p-4">
      {step.render(form)}
      {error ? (
        <p role="alert" className="mt-3 text-sm text-[color:var(--color-danger-zone)]">
          {error}
        </p>
      ) : null}
      <div className="mt-4 flex items-center justify-between">
        <button
          type="button"
          onClick={onBack}
          disabled={!canGoBack}
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground hover:bg-accent disabled:opacity-50"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={!form.formState.isValid || submitting}
          className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {isLast ? (submitting ? "Analyzing…" : "Analyze") : "Next"}
        </button>
      </div>
    </form>
  );
}

export function Field({
  label,
  htmlFor,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  error?: string;
  children: React.ReactNode;
}) {
  const errId = `${htmlFor}-error`;
  return (
    <div className="mb-3">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-foreground">
        {label}
      </label>
      <div className="mt-1">{children}</div>
      {error ? (
        <p id={errId} role="alert" className="mt-1 text-xs text-[color:var(--color-danger-zone)]">
          {error}
        </p>
      ) : null}
    </div>
  );
}
