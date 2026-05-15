#!/usr/bin/env node
/**
 * One-time script: open a browser, let the user log in to LinkedIn, then
 * save the storage state to the persistent context directory.
 * BUILD.md Task 2.6 / docs/LINKEDIN_SESSION.md
 */

import { chromium } from "playwright";
import { existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const CONTEXT_DIR = join(homedir(), "Library", "Application Support", "career-ops", "browser", "linkedin");
mkdirSync(CONTEXT_DIR, { recursive: true, mode: 0o700 });

const STATE_PATH = join(CONTEXT_DIR, "state.json");

const browser = await chromium.launch({ headless: false, channel: "chrome" });
const context = await browser.newContext();
const page = await context.newPage();

await page.goto("https://www.linkedin.com/login");
console.log("\nLog in to LinkedIn in the browser window that just opened.");
console.log("When you are fully logged in and can see your feed, CLOSE the browser window.\n");

// Wait for browser to be closed by user
await new Promise((resolve) => {
  browser.on("disconnected", resolve);
});

try {
  await context.storageState({ path: STATE_PATH });
  console.log(`Session saved to: ${STATE_PATH}`);
} catch (_) {
  console.log("Browser was closed — session may not have been saved cleanly.");
}
