#!/usr/bin/env node
/**
 * Lightweight health check until full career-ops Node tooling is merged from upstream.
 * BUILD.md Task −1.3 expects `npm run doctor` before extending the stack.
 */
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const required = [
  "BUILD.md",
  "pyproject.toml",
  "agents/__init__.py",
  "bridge/server.py",
  "flake.nix",
];

let failed = false;
for (const rel of required) {
  const p = resolve(root, rel);
  if (!existsSync(p)) {
    console.error(`[doctor] missing: ${rel}`);
    failed = true;
  }
}
if (failed) {
  process.exit(1);
}
console.log("[doctor] scaffold OK — extend checks when Node scanners from upstream are added.");
