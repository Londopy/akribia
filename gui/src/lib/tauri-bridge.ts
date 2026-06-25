// Typed wrappers around Tauri `invoke()` (spec 11.4) plus the debounce +
// request-ID guard the live-slider feature needs (spec 11.2). A Radix Slider
// fires onValueChange continuously while dragging; naively wiring that to invoke
// would fire a task re-run on every pixel and render stale results out of order.
import { invoke } from "@tauri-apps/api/core";

export interface ProfileInfo {
  name: string;
  prior_precision_cap: number | null;
  precision_flexibility: number;
  discount_factor: number;
  rpe_noise_std: number;
  forward_model_update_rate: number;
  injury_noise_std: number;
}

export const listProfiles = () => invoke<ProfileInfo[]>("list_profiles");
export const runIllusion = (priorPrecisionCap: number | null) =>
  invoke<number>("run_illusion", { priorPrecisionCap });
export const runVolatility = (precisionFlexibility: number) =>
  invoke<number[]>("run_volatility", { precisionFlexibility });
export const runDiscounting = (discountFactor: number) =>
  invoke<number[]>("run_discounting", { discountFactor });

/**
 * Debounce a value-producing async call (trailing edge) AND discard any in-flight
 * result that resolves after a newer call has started — the request-ID guard
 * (spec 11.2). This is the difference between "feels responsive" and "feels
 * broken" for the live-slider demo.
 */
export function makeDebouncedRunner<T>(
  fn: (value: number) => Promise<T>,
  onResult: (result: T) => void,
  onError: (message: string) => void,
  delayMs = 200
) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let latestRequestId = 0;

  return (value: number) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(async () => {
      const requestId = ++latestRequestId;
      try {
        const result = await fn(value);
        // Discard if a newer request has since been issued.
        if (requestId === latestRequestId) onResult(result);
      } catch (e) {
        if (requestId === latestRequestId) onError(String(e));
      }
    }, delayMs);
  };
}
