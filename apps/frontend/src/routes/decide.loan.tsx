import { createFileRoute } from "@tanstack/react-router";
import { LoanWizard } from "@/features/decide";

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
  component: () => <LoanWizard />,
});
