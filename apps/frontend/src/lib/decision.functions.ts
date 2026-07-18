import { createServerFn } from "@tanstack/react-start";
import { generateText, NoObjectGeneratedError, Output } from "ai";
import { createLovableAiGatewayProvider } from "@/lib/ai-gateway.server";
import {
  DecisionInputSchema,
  DecisionVerdictSchema,
  type DecisionInput,
  type DecisionVerdict,
} from "@/types/finance";

function amortizedPayment(principal: number, apr: number, termMonths: number): number {
  if (termMonths <= 0) return principal;
  const monthlyRate = apr / 100 / 12;
  if (monthlyRate === 0) return principal / termMonths;
  const factor = Math.pow(1 + monthlyRate, termMonths);
  return (principal * (monthlyRate * factor)) / (factor - 1);
}

function computeMetrics(input: DecisionInput): {
  monthlyImpact: number;
  savingsRunwayMonths: number;
  dtiPostChange: number;
} {
  if (input.kind === "purchase") {
    const monthly =
      input.paymentMethod === "financing" && input.apr !== undefined && input.termMonths
        ? amortizedPayment(input.price, input.apr, input.termMonths)
        : input.paymentMethod === "cash"
          ? 0
          : input.price;
    const cashOut = input.paymentMethod === "cash" ? input.price : 0;
    const remaining = Math.max(0, input.liquidSavings - cashOut);
    const runway =
      input.monthlyFixedExpenses > 0
        ? remaining / input.monthlyFixedExpenses
        : Number.POSITIVE_INFINITY;
    const dti =
      input.monthlyNetIncome > 0 ? monthly / input.monthlyNetIncome : 0;
    return {
      monthlyImpact: monthly,
      savingsRunwayMonths: Number.isFinite(runway) ? runway : 999,
      dtiPostChange: dti,
    };
  }

  const monthly = amortizedPayment(input.principal, input.apr, input.termMonths);
  const totalMonthlyDebt = input.existingMonthlyDebt + monthly;
  const dti =
    input.monthlyNetIncome > 0 ? totalMonthlyDebt / input.monthlyNetIncome : 0;
  const runway =
    input.monthlyNetIncome > 0
      ? input.liquidSavings / Math.max(1, monthly)
      : 0;
  return { monthlyImpact: monthly, savingsRunwayMonths: runway, dtiPostChange: dti };
}

export const analyzeDecision = createServerFn({ method: "POST" })
  .inputValidator((raw: unknown): DecisionInput => DecisionInputSchema.parse(raw))
  .handler(async ({ data }): Promise<DecisionVerdict> => {
    const metrics = computeMetrics(data);
    const key = process.env.LOVABLE_API_KEY;
    if (!key) {
      return {
        verdict: "wait",
        headline: "AI unavailable — deterministic estimate only",
        rationale: `Monthly impact ${metrics.monthlyImpact.toFixed(2)}, post-change DTI ${(metrics.dtiPostChange * 100).toFixed(1)}%, savings runway ${metrics.savingsRunwayMonths.toFixed(1)} months.`,
        monthlyImpact: metrics.monthlyImpact,
        savingsRunwayMonths: metrics.savingsRunwayMonths,
      };
    }

    const gateway = createLovableAiGatewayProvider(key);
    const model = gateway("google/gemini-3.5-flash");

    const summary =
      data.kind === "purchase"
        ? `Purchase decision. Item: ${data.itemName}. Price: ${data.price}. Payment: ${data.paymentMethod}. Urgency: ${data.urgency}. Monthly income: ${data.monthlyNetIncome}. Fixed expenses: ${data.monthlyFixedExpenses}. Liquid savings: ${data.liquidSavings}. Emergency fund months: ${data.emergencyFundMonths}.`
        : `Loan decision. Purpose: ${data.purpose}. Principal: ${data.principal}. APR: ${data.apr}. Term: ${data.termMonths}. Existing monthly debt: ${data.existingMonthlyDebt}. Monthly income: ${data.monthlyNetIncome}. Liquid savings: ${data.liquidSavings}.`;

    const prompt = `${summary}
Deterministic metrics: monthlyImpact=${metrics.monthlyImpact.toFixed(2)}, savingsRunwayMonths=${metrics.savingsRunwayMonths.toFixed(2)}, dtiPostChange=${metrics.dtiPostChange.toFixed(3)}.
Return a JSON verdict object. Set monthlyImpact and savingsRunwayMonths to exactly the values given. Keep rationale under 400 characters.`;

    try {
      const { output } = await generateText({
        model,
        system:
          "You are MoneyOS, a conservative financial advisor. Respond only with the requested JSON object.",
        prompt,
        output: Output.object({ schema: DecisionVerdictSchema }),
      });
      return {
        ...output,
        monthlyImpact: metrics.monthlyImpact,
        savingsRunwayMonths: metrics.savingsRunwayMonths,
      };
    } catch (error) {
      if (NoObjectGeneratedError.isInstance(error)) {
        return {
          verdict: "wait",
          headline: "Could not generate structured verdict",
          rationale: `Deterministic result: monthly impact ${metrics.monthlyImpact.toFixed(2)}, DTI ${(metrics.dtiPostChange * 100).toFixed(1)}%.`,
          monthlyImpact: metrics.monthlyImpact,
          savingsRunwayMonths: metrics.savingsRunwayMonths,
        };
      }
      throw error;
    }
  });
