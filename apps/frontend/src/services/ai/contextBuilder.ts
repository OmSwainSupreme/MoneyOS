import type { AIMessage } from "@/types/finance";
import { MESSAGE_WINDOW } from "@/lib/store/aiStore";
import { scrubText, type ScrubResult } from "./pii";

export interface FinanceDigest {
  monthlyNetIncome: number;
  monthlyExpenses: number;
  netCashFlow: number;
  savingsRate: number;
  dti: number;
  assetLiabilityRatio: number;
  liquidSavings: number;
}

export interface OutgoingMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface BuildContextArgs {
  systemPrompt: string;
  digest: FinanceDigest;
  history: AIMessage[];
  rollingSummary: string;
  seedAliases?: Record<string, string>;
}

export interface BuildContextResult {
  messages: OutgoingMessage[];
  aliases: Record<string, string>;
}

function messageText(m: AIMessage): string {
  return m.parts.map((p) => p.text).join("");
}

function formatDigest(d: FinanceDigest): string {
  return [
    `Monthly net income: ${d.monthlyNetIncome.toFixed(2)}`,
    `Monthly expenses: ${d.monthlyExpenses.toFixed(2)}`,
    `Net cash flow: ${d.netCashFlow.toFixed(2)}`,
    `Savings rate: ${(d.savingsRate * 100).toFixed(1)}%`,
    `Debt-to-income: ${(d.dti * 100).toFixed(1)}%`,
    `Asset/liability ratio: ${
      Number.isFinite(d.assetLiabilityRatio) ? d.assetLiabilityRatio.toFixed(2) : "n/a"
    }`,
    `Liquid savings: ${d.liquidSavings.toFixed(2)}`,
  ].join("\n");
}

export function buildContext(args: BuildContextArgs): BuildContextResult {
  const trimmed = args.history.slice(-MESSAGE_WINDOW);
  const aliases: Record<string, string> = { ...(args.seedAliases ?? {}) };

  const scrub = (text: string): string => {
    const result: ScrubResult = scrubText(text, aliases);
    Object.assign(aliases, result.aliases);
    return result.text;
  };

  const systemParts = [
    args.systemPrompt,
    `Financial digest (numeric only, already de-identified):\n${formatDigest(args.digest)}`,
  ];
  if (args.rollingSummary.trim()) {
    systemParts.push(`Rolling summary of earlier turns:\n${scrub(args.rollingSummary)}`);
  }

  const messages: OutgoingMessage[] = [
    { role: "system", content: systemParts.join("\n\n") },
    ...trimmed.map((m) => ({
      role: m.role,
      content: scrub(messageText(m)),
    })),
  ];

  return { messages, aliases };
}
