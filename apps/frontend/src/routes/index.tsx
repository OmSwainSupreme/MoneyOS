import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: Landing,
});

function Landing() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
        Clear financial decisions, backed by your own numbers.
      </h1>
      <p className="mt-4 text-base text-muted-foreground">
        MoneyOS ingests your cash flow and liabilities, tracks overspending in real
        time, and stress-tests purchases and loans before you commit. Nothing leaves
        your browser unless you explicitly ask the assistant.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          to="/dashboard"
          className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Open dashboard
        </Link>
        <Link
          to="/import"
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium text-foreground hover:bg-accent"
        >
          Import a statement
        </Link>
      </div>
      <section className="mt-12 grid gap-4 sm:grid-cols-2">
        <FeatureCard
          title="High-trust dashboard"
          body="Net cash flow, savings rate, overspend alarms, and asset/liability ratio at a glance."
        />
        <FeatureCard
          title="Sandboxed import"
          body="CSV or JSON parsed entirely in-browser with row-level validation before anything is stored."
        />
        <FeatureCard
          title="Decision wizards"
          body='Structured "Can I buy this?" and "Should I take this loan?" flows with typed inputs.'
        />
        <FeatureCard
          title="Bounded AI"
          body="Chat context is scrubbed of names, emails, phone and account numbers at the client boundary."
        />
      </section>
    </div>
  );
}

function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-semibold text-card-foreground">{title}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{body}</p>
    </div>
  );
}
