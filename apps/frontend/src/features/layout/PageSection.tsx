import type { ReactNode } from "react";

// Shared page header + padded container used across routes to remove the
// repeated <header> + max-w-* boilerplate. Does not touch __root.tsx nav.

const MAX_WIDTHS = {
  sm: "max-w-2xl",
  md: "max-w-3xl",
  lg: "max-w-4xl",
  xl: "max-w-6xl",
  full: "max-w-none",
} as const;

export type PageSectionWidth = keyof typeof MAX_WIDTHS;

export function PageSection({
  title,
  description,
  maxWidth = "xl",
  actions,
  children,
  className,
}: {
  title: string;
  description?: string;
  maxWidth?: PageSectionWidth;
  actions?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mx-auto ${MAX_WIDTHS[maxWidth]} px-4 py-8 sm:px-6 ${className ?? ""}`}>
      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
          {description ? (
            <p className="text-sm text-muted-foreground">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </header>
      {children}
    </div>
  );
}
