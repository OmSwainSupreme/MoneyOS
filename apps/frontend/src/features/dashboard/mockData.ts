// Dashboard seed-data loader seam.
// The dashboard feature owns this loader; the raw typed data lives in
// `src/features/shared/mock/finance.ts`. When a real backend exists,
// only this function changes.

import { mockFinanceSnapshot } from "@/features/shared/mock/finance";

export function getDashboardSeedData() {
  // TODO(backend): replace with a fetch from the finance snapshot endpoint,
  // e.g. `const res = await fetch("/api/finance/snapshot"); return res.json();`
  return mockFinanceSnapshot;
}
