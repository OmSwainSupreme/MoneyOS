import { createFileRoute } from "@tanstack/react-router";
import { PurchaseWizard } from "@/features/decide";

export const Route = createFileRoute("/decide/purchase")({
  head: () => ({
    meta: [
      { title: "Can I buy this? · MoneyOS" },
      {
        name: "description",
        content: "Stress-test a purchase against your income, savings, and monthly obligations.",
      },
      { property: "og:title", content: "Can I buy this? · MoneyOS" },
      {
        property: "og:description",
        content: "Structured multi-step check before you commit to a purchase.",
      },
    ],
  }),
  component: () => <PurchaseWizard />,
});
