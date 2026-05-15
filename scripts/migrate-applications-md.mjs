#!/usr/bin/env node
/**
 * Add new columns to data/applications.md (idempotent — safe to run twice).
 * BUILD.md Task 1.9
 *
 * New columns appended (after existing headers, never inserted mid-table):
 *   apply_status | apply_run_id | track | gate_log | screenshot_dir
 */

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const appsPath = resolve(root, "data", "applications.md");

const NEW_COLS = ["apply_status", "apply_run_id", "track", "gate_log", "screenshot_dir"];

if (!existsSync(appsPath)) {
  console.log("[migrate] data/applications.md not found — creating stub.");
  const stub = [
    "# Applications",
    "",
    "| company | role | url | date | status | apply_status | apply_run_id | track | gate_log | screenshot_dir |",
    "|---------|------|-----|------|--------|--------------|--------------|-------|----------|----------------|",
    "",
  ].join("\n");
  writeFileSync(appsPath, stub, "utf8");
  console.log("[migrate] Created stub data/applications.md");
  process.exit(0);
}

let content = readFileSync(appsPath, "utf8");
const lines = content.split("\n");

// Find the header line (first line containing "|")
const headerIdx = lines.findIndex((l) => l.trim().startsWith("|"));
if (headerIdx === -1) {
  console.log("[migrate] No table found in applications.md — skipping.");
  process.exit(0);
}

const header = lines[headerIdx];
let changed = false;

for (const col of NEW_COLS) {
  if (!header.toLowerCase().includes(col.toLowerCase())) {
    lines[headerIdx] = lines[headerIdx].trimEnd() + ` ${col} |`;
    // Extend separator line too
    const sepIdx = headerIdx + 1;
    if (sepIdx < lines.length && lines[sepIdx].includes("---")) {
      lines[sepIdx] = lines[sepIdx].trimEnd() + " --- |";
    }
    changed = true;
    console.log(`[migrate] Added column: ${col}`);
  } else {
    console.log(`[migrate] Column already present: ${col}`);
  }
}

if (changed) {
  writeFileSync(appsPath, lines.join("\n"), "utf8");
  console.log("[migrate] data/applications.md updated.");
} else {
  console.log("[migrate] No changes needed.");
}
