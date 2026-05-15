# LinkedIn session capture (one-time)

The LinkedIn adapter requires a persistent logged-in browser context.

## Steps

1. Install playwright browsers if not already done:
   ```bash
   uv run playwright install chromium
   ```

2. Run the session capture script:
   ```bash
   node scripts/save-linkedin-session.mjs
   ```
   This opens a Chrome window. Log in to LinkedIn normally. Close the window when done.

3. The session state is saved at:
   `~/Library/Application Support/career-ops/browser/linkedin/state.json`

## Maintenance

Sessions expire. The healthcheck (`make health-check`) runs every 6 h and alerts via WhatsApp when the session is stale.

## Hard rules

- **Never** scrape profiles.
- **Never** create fake accounts.
- Easy Apply flows only, at ≤8/hr, ≤25/day.
- On any "restricted" or "verify you're human" page, the adapter halts LinkedIn source for 60 min and sends a WhatsApp critical alert.
