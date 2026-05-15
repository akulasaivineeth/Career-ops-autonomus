# Legal disclaimer

## Not legal advice

This software assists with **job search workflow automation**. It is not legal, immigration, or employment advice. You are responsible for compliance with:

- Each employer’s and ATS provider’s **Terms of Service** and **robots / automation policies**.
- **LinkedIn** and other platforms’ rules (including limits on automated access).
- Applicable **privacy**, **anti-spam**, and **employment** laws in your jurisdiction.

## Autonomous mode warning

When autonomy features are enabled (`docs/AUTONOMY.md`, future releases), the system may propose or prepare applications. **You remain liable** for submitted content and for any account restrictions vendors impose.

## No warranty

The software is provided **as-is** without warranty of fitness for a particular purpose. Use at your own risk.

## Platform-specific automation risks

- **LinkedIn:** Use only legitimate logged-in sessions and product flows you are permitted to use (e.g. Easy Apply where applicable). Do **not** scrape member profiles or circumvent technical controls. Respect rate limits in `docs/AUTONOMY.md` / architecture doc §E.
- **Workday and similar enterprise ATS:** Anti-bot systems may lock accounts. Prefer conservative cadence, persistent browser contexts, and human escalation on repeated challenges.
- **One human, one identity:** No parallel fake identities, no proxy rotation to multiply accounts, and no evasion of vendor enforcement signals (see architecture §E.2).

