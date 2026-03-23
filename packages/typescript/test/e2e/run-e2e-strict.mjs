/**
 * Runs the TypeScript E2E suite with E2E_STRICT=1 so missing KWEAVER_BASE_URL
 * fails in ensure-token.ts instead of running an all-skipped suite.
 */
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const pkgRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const env = { ...process.env, E2E_STRICT: "1" };
const node = process.execPath;

let r = spawnSync(node, ["--import", "tsx", "test/e2e/ensure-token.ts"], {
  cwd: pkgRoot,
  stdio: "inherit",
  env,
});
if (r.status !== 0) process.exit(r.status ?? 1);

r = spawnSync(
  node,
  ["--import", "tsx", "--test", "--test-concurrency=1", "test/e2e/**/*.test.ts"],
  { cwd: pkgRoot, stdio: "inherit", env, shell: true },
);
process.exit(r.status ?? 1);
