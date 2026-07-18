import { d as TSS_SERVER_FUNCTION, t as createServerFn } from "./createServerFn-D40y8WyT.js";
import { n as DecisionVerdictSchema, t as DecisionInputSchema } from "./finance-BjdKDlHX.js";
import { NoObjectGeneratedError, Output, generateText } from "ai";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
//#region ../../node_modules/@tanstack/start-server-core/dist/esm/createServerRpc.js
var createServerRpc = (serverFnMeta, splitImportFn) => {
	const url = "/_serverFn/" + serverFnMeta.id;
	return Object.assign(splitImportFn, {
		url,
		serverFnMeta,
		[TSS_SERVER_FUNCTION]: true
	});
};
//#endregion
//#region src/lib/ai-gateway.server.ts
function createLovableAiGatewayProvider(apiKey) {
	return createOpenAICompatible({
		name: "lovable",
		baseURL: "https://ai.gateway.lovable.dev/v1",
		headers: {
			"Lovable-API-Key": apiKey,
			"X-Lovable-AIG-SDK": "vercel-ai-sdk"
		}
	});
}
//#endregion
//#region src/lib/decision.functions.ts?tss-serverfn-split
function amortizedPayment(principal, apr, termMonths) {
	if (termMonths <= 0) return principal;
	const monthlyRate = apr / 100 / 12;
	if (monthlyRate === 0) return principal / termMonths;
	const factor = Math.pow(1 + monthlyRate, termMonths);
	return principal * (monthlyRate * factor) / (factor - 1);
}
function computeMetrics(input) {
	if (input.kind === "purchase") {
		const monthly = input.paymentMethod === "financing" && input.apr !== void 0 && input.termMonths ? amortizedPayment(input.price, input.apr, input.termMonths) : input.paymentMethod === "cash" ? 0 : input.price;
		const cashOut = input.paymentMethod === "cash" ? input.price : 0;
		const remaining = Math.max(0, input.liquidSavings - cashOut);
		const runway = input.monthlyFixedExpenses > 0 ? remaining / input.monthlyFixedExpenses : Number.POSITIVE_INFINITY;
		const dti = input.monthlyNetIncome > 0 ? monthly / input.monthlyNetIncome : 0;
		return {
			monthlyImpact: monthly,
			savingsRunwayMonths: Number.isFinite(runway) ? runway : 999,
			dtiPostChange: dti
		};
	}
	const monthly = amortizedPayment(input.principal, input.apr, input.termMonths);
	const totalMonthlyDebt = input.existingMonthlyDebt + monthly;
	const dti = input.monthlyNetIncome > 0 ? totalMonthlyDebt / input.monthlyNetIncome : 0;
	return {
		monthlyImpact: monthly,
		savingsRunwayMonths: input.monthlyNetIncome > 0 ? input.liquidSavings / Math.max(1, monthly) : 0,
		dtiPostChange: dti
	};
}
var analyzeDecision_createServerFn_handler = createServerRpc({
	id: "c90455b75509e343d8ff38c8f80c3279564e3028cdfe7da2fa885c25938b116e",
	name: "analyzeDecision",
	filename: "src/lib/decision.functions.ts"
}, (opts) => analyzeDecision.__executeServer(opts));
var analyzeDecision = createServerFn({ method: "POST" }).inputValidator((raw) => DecisionInputSchema.parse(raw)).handler(analyzeDecision_createServerFn_handler, async ({ data }) => {
	const metrics = computeMetrics(data);
	const key = process.env.LOVABLE_API_KEY;
	if (!key) return {
		verdict: "wait",
		headline: "AI unavailable — deterministic estimate only",
		rationale: `Monthly impact ${metrics.monthlyImpact.toFixed(2)}, post-change DTI ${(metrics.dtiPostChange * 100).toFixed(1)}%, savings runway ${metrics.savingsRunwayMonths.toFixed(1)} months.`,
		monthlyImpact: metrics.monthlyImpact,
		savingsRunwayMonths: metrics.savingsRunwayMonths
	};
	const model = createLovableAiGatewayProvider(key)("google/gemini-3.5-flash");
	const prompt = `${data.kind === "purchase" ? `Purchase decision. Item: ${data.itemName}. Price: ${data.price}. Payment: ${data.paymentMethod}. Urgency: ${data.urgency}. Monthly income: ${data.monthlyNetIncome}. Fixed expenses: ${data.monthlyFixedExpenses}. Liquid savings: ${data.liquidSavings}. Emergency fund months: ${data.emergencyFundMonths}.` : `Loan decision. Purpose: ${data.purpose}. Principal: ${data.principal}. APR: ${data.apr}. Term: ${data.termMonths}. Existing monthly debt: ${data.existingMonthlyDebt}. Monthly income: ${data.monthlyNetIncome}. Liquid savings: ${data.liquidSavings}.`}
Deterministic metrics: monthlyImpact=${metrics.monthlyImpact.toFixed(2)}, savingsRunwayMonths=${metrics.savingsRunwayMonths.toFixed(2)}, dtiPostChange=${metrics.dtiPostChange.toFixed(3)}.
Return a JSON verdict object. Set monthlyImpact and savingsRunwayMonths to exactly the values given. Keep rationale under 400 characters.`;
	try {
		const { output } = await generateText({
			model,
			system: "You are MoneyOS, a conservative financial advisor. Respond only with the requested JSON object.",
			prompt,
			output: Output.object({ schema: DecisionVerdictSchema })
		});
		return {
			...output,
			monthlyImpact: metrics.monthlyImpact,
			savingsRunwayMonths: metrics.savingsRunwayMonths
		};
	} catch (error) {
		if (NoObjectGeneratedError.isInstance(error)) return {
			verdict: "wait",
			headline: "Could not generate structured verdict",
			rationale: `Deterministic result: monthly impact ${metrics.monthlyImpact.toFixed(2)}, DTI ${(metrics.dtiPostChange * 100).toFixed(1)}%.`,
			monthlyImpact: metrics.monthlyImpact,
			savingsRunwayMonths: metrics.savingsRunwayMonths
		};
		throw error;
	}
});
//#endregion
export { analyzeDecision_createServerFn_handler };
