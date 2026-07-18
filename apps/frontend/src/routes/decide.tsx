import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/decide")({
  component: DecideLayout,
});

function DecideLayout() {
  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6">
      <Outlet />
    </main>
  );
}
