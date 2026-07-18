import { z } from "zod";

const isoDate = z.string().datetime({ offset: true });

export const CurrencySchema = z.enum(["USD", "EUR", "GBP", "CAD", "AUD"]);
export type Currency = z.infer<typeof CurrencySchema>;

export const TransactionCategorySchema = z.enum([
  "income",
  "housing",
  "food",
  "transport",
  "utilities",
  "entertainment",
  "health",
  "shopping",
  "savings",
  "debt",
  "other",
]);
export type TransactionCategory = z.infer<typeof TransactionCategorySchema>;

export const TransactionSchema = z.object({
  id: z.string().min(1),
  date: isoDate,
  amount: z.number().finite(),
  currency: CurrencySchema.default("USD"),
  category: TransactionCategorySchema.default("other"),
  merchant: z.string().trim().max(200).default(""),
  source: z.enum(["bank", "manual", "import"]).default("import"),
  rawDescription: z.string().max(500).optional(),
});
export type Transaction = z.infer<typeof TransactionSchema>;

export const LiabilitySchema = z.object({
  id: z.string().min(1),
  name: z.string().trim().min(1).max(120),
  principal: z.number().finite().nonnegative(),
  apr: z.number().finite().min(0).max(100),
  termMonths: z.number().int().min(1).max(600),
  minPayment: z.number().finite().nonnegative(),
  startDate: isoDate,
});
export type Liability = z.infer<typeof LiabilitySchema>;

export const AssetSchema = z.object({
  id: z.string().min(1),
  name: z.string().trim().min(1).max(120),
  type: z.enum(["cash", "investment", "property", "other"]),
  value: z.number().finite().nonnegative(),
  asOf: isoDate,
});
export type Asset = z.infer<typeof AssetSchema>;

export const BudgetEntrySchema = z.object({
  id: z.string().min(1),
  category: TransactionCategorySchema,
  monthlyLimit: z.number().finite().nonnegative(),
  rollover: z.boolean().default(false),
});
export type BudgetEntry = z.infer<typeof BudgetEntrySchema>;

export const IncomeSchema = z.object({
  id: z.string().min(1),
  source: z.string().trim().min(1).max(120),
  monthlyNet: z.number().finite().nonnegative(),
  cadence: z.enum(["monthly", "biweekly", "weekly"]).default("monthly"),
});
export type Income = z.infer<typeof IncomeSchema>;

export const AIMessagePartSchema = z.object({
  type: z.literal("text"),
  text: z.string(),
});
export type AIMessagePart = z.infer<typeof AIMessagePartSchema>;

export const AIMessageSchema = z.object({
  id: z.string().min(1),
  role: z.enum(["user", "assistant", "system"]),
  parts: z.array(AIMessagePartSchema).min(1),
  createdAt: isoDate,
  scrubbed: z.boolean().default(false),
});
export type AIMessage = z.infer<typeof AIMessageSchema>;

export const PurchaseDecisionInputSchema = z.object({
  kind: z.literal("purchase"),
  itemName: z.string().trim().min(1).max(120),
  price: z.number().finite().positive(),
  urgency: z.enum(["now", "3m", "12m"]),
  paymentMethod: z.enum(["cash", "credit", "financing"]),
  apr: z.number().finite().min(0).max(100).optional(),
  termMonths: z.number().int().min(1).max(600).optional(),
  monthlyNetIncome: z.number().finite().nonnegative(),
  monthlyFixedExpenses: z.number().finite().nonnegative(),
  liquidSavings: z.number().finite().nonnegative(),
  emergencyFundMonths: z.number().finite().min(0).max(60),
});
export type PurchaseDecisionInput = z.infer<typeof PurchaseDecisionInputSchema>;

export const LoanDecisionInputSchema = z.object({
  kind: z.literal("loan"),
  principal: z.number().finite().positive(),
  apr: z.number().finite().min(0).max(100),
  termMonths: z.number().int().min(1).max(600),
  purpose: z.string().trim().min(1).max(200),
  existingMonthlyDebt: z.number().finite().nonnegative(),
  monthlyNetIncome: z.number().finite().nonnegative(),
  liquidSavings: z.number().finite().nonnegative(),
});
export type LoanDecisionInput = z.infer<typeof LoanDecisionInputSchema>;

export const DecisionInputSchema = z.discriminatedUnion("kind", [
  PurchaseDecisionInputSchema,
  LoanDecisionInputSchema,
]);
export type DecisionInput = z.infer<typeof DecisionInputSchema>;

export const DecisionVerdictSchema = z.object({
  verdict: z.enum(["yes", "wait", "no"]),
  headline: z.string().min(1).max(200),
  rationale: z.string().min(1).max(2000),
  monthlyImpact: z.number().finite(),
  savingsRunwayMonths: z.number().finite().nonnegative(),
});
export type DecisionVerdict = z.infer<typeof DecisionVerdictSchema>;
