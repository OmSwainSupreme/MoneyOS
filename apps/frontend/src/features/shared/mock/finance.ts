// Pure mock finance data for the MoneyOS frontend demos and tests.
// IMPORTANT: this module imports only *types* from `@/types/finance`.
// It must never import the finance store — features own the loader seam,
// this file is just the data source. Keeping it store-free avoids a
// circular import (store <-> feature mock) that would blank the app.

import type {
  Asset,
  BudgetEntry,
  Income,
  Liability,
  Transaction,
  TransactionCategory,
} from "@/types/finance";

const DAY_MS = 24 * 60 * 60 * 1000;

// ISO datetime within the last `daysAgo` days (current-month so the
// month-to-date selectors produce non-trivial output).
function isoDaysAgo(daysAgo: number): string {
  return new Date(Date.now() - daysAgo * DAY_MS).toISOString();
}

function tx(
  daysAgo: number,
  amount: number,
  category: TransactionCategory,
  merchant: string,
): Transaction {
  return {
    id: crypto.randomUUID(),
    date: isoDaysAgo(daysAgo),
    amount,
    currency: "USD",
    category,
    merchant,
    source: "import",
  };
}

export const mockTransactions: Transaction[] = [
  // Income (positive amounts)
  tx(28, 4200, "income", "Acme Corp Payroll"),
  tx(14, 4200, "income", "Acme Corp Payroll"),
  tx(2, 120, "income", "Freelance gig"),
  // Housing
  tx(27, -1650, "housing", "Greenfield Apartments"),
  tx(13, -1650, "housing", "Greenfield Apartments"),
  // Food — intentionally over budget (limit is 700)
  tx(20, -320, "food", "Whole Foods"),
  tx(16, -210, "food", "Blue Bottle"),
  tx(10, -260, "food", "Trader Joe's"),
  tx(6, -240, "food", "DoorDash"),
  tx(2, -190, "food", "Local Bistro"),
  // Transport
  tx(25, -85, "transport", "Shell"),
  tx(18, -120, "transport", "Uber"),
  tx(9, -95, "transport", "Metro Card"),
  // Utilities
  tx(22, -140, "utilities", "City Power"),
  tx(22, -65, "utilities", "AquaFlow"),
  // Entertainment
  tx(19, -45, "entertainment", "Spotify"),
  tx(12, -16, "entertainment", "Steam"),
  tx(7, -80, "entertainment", "AMC Theatres"),
  // Health
  tx(17, -60, "health", "CVS Pharmacy"),
  tx(4, -35, "health", "Gym Membership"),
  // Shopping
  tx(21, -130, "shopping", "Amazon"),
  tx(11, -75, "shopping", "Uniqlo"),
  tx(3, -210, "shopping", "Apple Store"),
  // Savings — positive contribution to savings bucket
  tx(15, -500, "savings", "Vanguard IRA"),
  // Debt — min payments
  tx(23, -310, "debt", "Chase Card"),
  tx(8, -240, "debt", "Discover"),
  // Other
  tx(5, -42, "other", "Post Office"),
];

export const mockAssets: Asset[] = [
  {
    id: crypto.randomUUID(),
    name: "Everyday Checking",
    type: "cash",
    value: 6400,
    asOf: isoDaysAgo(1),
  },
  {
    id: crypto.randomUUID(),
    name: "High-Yield Savings",
    type: "cash",
    value: 18500,
    asOf: isoDaysAgo(1),
  },
  {
    id: crypto.randomUUID(),
    name: "Brokerage",
    type: "investment",
    value: 31200,
    asOf: isoDaysAgo(1),
  },
];

export const mockLiabilities: Liability[] = [
  {
    id: crypto.randomUUID(),
    name: "Chase Sapphire",
    principal: 4200,
    apr: 21.99,
    termMonths: 36,
    minPayment: 160,
    startDate: isoDaysAgo(120),
  },
  {
    id: crypto.randomUUID(),
    name: "Discover It",
    principal: 2600,
    apr: 18.24,
    termMonths: 24,
    minPayment: 95,
    startDate: isoDaysAgo(90),
  },
  {
    id: crypto.randomUUID(),
    name: "Auto Loan",
    principal: 11200,
    apr: 5.49,
    termMonths: 48,
    minPayment: 265,
    startDate: isoDaysAgo(400),
  },
];

export const mockBudgets: BudgetEntry[] = [
  {
    id: crypto.randomUUID(),
    category: "food",
    monthlyLimit: 700,
    rollover: false,
  },
  {
    id: crypto.randomUUID(),
    category: "transport",
    monthlyLimit: 300,
    rollover: false,
  },
  {
    id: crypto.randomUUID(),
    category: "entertainment",
    monthlyLimit: 150,
    rollover: false,
  },
  {
    id: crypto.randomUUID(),
    category: "shopping",
    monthlyLimit: 400,
    rollover: false,
  },
];

export const mockIncomes: Income[] = [
  {
    id: crypto.randomUUID(),
    source: "Acme Corp",
    monthlyNet: 4200,
    cadence: "monthly",
  },
  {
    id: crypto.randomUUID(),
    source: "Freelance",
    monthlyNet: 180,
    cadence: "monthly",
  },
];

export const mockFinanceSnapshot = {
  transactions: mockTransactions,
  assets: mockAssets,
  liabilities: mockLiabilities,
  budgets: mockBudgets,
  incomes: mockIncomes,
};

export type MockFinanceSnapshot = typeof mockFinanceSnapshot;
