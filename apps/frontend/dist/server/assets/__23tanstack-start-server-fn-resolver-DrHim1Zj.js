//#region \0%23tanstack-start-server-fn-resolver
var manifest = { "c90455b75509e343d8ff38c8f80c3279564e3028cdfe7da2fa885c25938b116e": {
	functionName: "analyzeDecision_createServerFn_handler",
	importer: () => import("./decision.functions-BEhcE88U.js")
} };
async function getServerFnById(id, access) {
	const serverFnInfo = manifest[id];
	if (!serverFnInfo) throw new Error("Server function info not found for " + id);
	const fnModule = serverFnInfo.module ?? await serverFnInfo.importer();
	if (!fnModule) throw new Error("Server function module not resolved for " + id);
	const action = fnModule[serverFnInfo.functionName];
	if (!action) throw new Error("Server function module export not resolved for serverFn ID: " + id);
	return action;
}
//#endregion
export { getServerFnById as t };
