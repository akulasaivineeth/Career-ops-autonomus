# WhatsApp Cloud API setup

1. Go to [developers.facebook.com](https://developers.facebook.com) → Create app → Business.
2. Add **WhatsApp** product → API Setup.
3. Get your **Phone Number ID** and generate a **permanent access token** via System Users.
4. Set environment variables (in `.envrc` or shell):
   ```bash
   export WA_PHONE_NUMBER_ID=<your-phone-number-id>
   export WA_USER_NUMBER=+1XXXXXXXXXX      # your personal WhatsApp number
   export WA_WEBHOOK_VERIFY_TOKEN=<32+ char random string>
   ```
5. Store the access token in Keychain:
   ```bash
   read -s VAL && security add-generic-password -U \
     -s careerops.whatsapp -a access_token -w "$VAL" && unset VAL && echo stored
   ```
6. Expose local bridge for webhook:
   ```bash
   brew install cloudflared
   cloudflared tunnel --url http://127.0.0.1:8765
   ```
7. Set webhook URL in Meta dashboard: `https://<your-tunnel>.trycloudflare.com/webhook/whatsapp`
   - Verify token: the value of `WA_WEBHOOK_VERIFY_TOKEN`.
   - Subscribe to `messages` field.

After setup, test with:
```bash
uv run python -c "from agents.tools.whatsapp import send_text; send_text('career-ops alive')"
```
