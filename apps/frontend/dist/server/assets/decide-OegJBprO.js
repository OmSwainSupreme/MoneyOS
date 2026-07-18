import { Outlet } from "@tanstack/react-router";
import { jsx } from "react/jsx-runtime";
//#region src/routes/decide.tsx?tsr-split=component
function DecideLayout() {
	return /* @__PURE__ */ jsx("main", {
		className: "mx-auto w-full max-w-4xl px-4 py-8 sm:px-6",
		children: /* @__PURE__ */ jsx(Outlet, {})
	});
}
//#endregion
export { DecideLayout as component };
