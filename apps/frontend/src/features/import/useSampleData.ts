// Helper for loading the canned sample statement into the finance store
// without a file upload — mirrors the import flow for quick demos.

import { useFinanceStore } from "@/lib/store/financeStore";
import {
  downloadSample,
  sampleTransactions,
} from "./sampleStatement";

export function useSampleData() {
  const addTransactions = useFinanceStore((s) => s.addTransactions);

  const loadSample = () => {
    // TODO(backend): replace this client-side merge with a server upload
    // + reconcile flow once the import API exists.
    addTransactions(sampleTransactions);
  };

  return { loadSample, downloadSample };
}
