// Realistic default seed values for the decision wizards so the forms
// are not blank on load. These mirror the shape of the zod-inferred
// purchase/loan inputs but are partial — the route keeps the rest of
// its step defaults.

import type { LoanDecisionInput, PurchaseDecisionInput } from "@/types/finance";

export const purchaseSeed: Partial<PurchaseDecisionInput> = {
  itemName: "New laptop",
  price: 1200,
  urgency: "3m",
  paymentMethod: "credit",
  monthlyNetIncome: 4200,
  monthlyFixedExpenses: 2600,
  liquidSavings: 9000,
  emergencyFundMonths: 4,
};

export const loanSeed: Partial<LoanDecisionInput> = {
  principal: 15000,
  apr: 6.5,
  termMonths: 48,
  purpose: "Car refinance",
  existingMonthlyDebt: 400,
  monthlyNetIncome: 4200,
  liquidSavings: 9000,
};
