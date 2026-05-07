import { defineConfig } from "eslint/config";
import next from "eslint-config-next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig([
  {
    ignores: [".next-dev/**", ".next/**", "dist/**", "node_modules/**"]
  },
  {
    extends: [...next],
  },
  {
    // React Compiler-era strict rules ("set-state-in-effect", "purity",
    // "preserve-manual-memoization") flag legitimate one-shot patterns
    // (URL parse failure → error state, Date.now in render). Downgrade to
    // warn while migration epic is in flight; original errors remain visible
    // in CI logs without blocking main.
    rules: {
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/purity": "warn",
      "react-hooks/preserve-manual-memoization": "warn",
    },
  },
  {
    // Playwright e2e tests use `use()` from @playwright/test — collides with
    // React Hook naming rule. Tests are not React components, scope rule off.
    files: ["e2e/**/*.{ts,tsx}"],
    rules: {
      "react-hooks/rules-of-hooks": "off",
    },
  }
]);
