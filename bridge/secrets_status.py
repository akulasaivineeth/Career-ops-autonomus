"""
Check which Keychain secrets are present (existence only — values never read here).
Used by the dashboard secrets tab.
"""

from __future__ import annotations


def get_secrets_status() -> list[dict[str, object]]:
    """Return a list of {label, service, account, ok} dicts."""
    from agents.tools.keychain import get_secret

    checks = [
        ("Anthropic API key", "anthropic", "api_key", True),
        ("Gmail OAuth token", "gmail", "oauth_token_json", True),
        ("WhatsApp token", "whatsapp", "access_token", True),
        ("CapSolver key", "capsolver", "api_key", False),
        ("2Captcha key", "twocaptcha", "api_key", False),
        ("SQLCipher passphrase", "db", "encryption_key", False),
    ]

    result = []
    for label, name, account, required in checks:
        val = get_secret(name, account)
        result.append(
            {
                "label": label,
                "service": f"careerops.{name}",
                "account": account,
                "required": required,
                "ok": val is not None,
            }
        )
    return result
