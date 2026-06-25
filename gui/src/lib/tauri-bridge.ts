// Compatibility shim — superseded by ./engine.ts. Re-exports so any lingering
// import keeps working. New code should import from "@/lib/engine".
export { engine, makeDebouncedRunner, BACKEND } from "./engine";
export type { ProfileInfo } from "./profiles";
