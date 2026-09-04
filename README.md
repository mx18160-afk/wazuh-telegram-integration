# Wazuh → Telegram Alert Integration

A custom Wazuh integration that forwards File Integrity Monitoring (FIM) and
malware/rootcheck alerts to a Telegram chat in real time.

## Overview

Wazuh natively supports integrations with services like Slack and VirusTotal,
but doesn't ship a Telegram integration out of the box. This project adds one:
whenever Wazuh's manager generates an alert matching FIM, rootcheck, malware,
or VirusTotal rule groups, this tool formats the alert and pushes it to a
Telegram chat, giving analysts instant mobile notifications instead of having
to watch the dashboard.

## How it works

```
Wazuh Manager
     │  (alert matches configured level/rule)
     ▼
/var/ossec/integrations/custom-telegram   (wrapper script)
     │  invokes with Wazuh's bundled Python
     ▼
/var/ossec/integrations/custom-telegram.py
     │  1. reads the alert JSON
     │  2. filters for relevant rule groups
     │  3. formats a human-readable message
     │  4. POSTs to Telegram Bot API (with retries)
     ▼
Telegram chat / group
```

Wazuh invokes integrations automatically — no polling, no cron job. The
manager calls the script the moment a matching alert is generated.

## Files

| File | Purpose |
|---|---|
| `custom-telegram.py` | Main integration logic: reads, filters, formats, and sends the alert |
| `custom-telegram` | Shell wrapper Wazuh actually executes; locates and calls the Python script with the manager's bundled interpreter |
| `SETUP.md` | Step-by-step installation and configuration instructions |

## Requirements

- Wazuh manager (tested against Wazuh 4.x)
- Outbound HTTPS access from the manager to `api.telegram.org`
- `requests` library installed into Wazuh's bundled Python environment
- A Telegram bot token and target chat ID

## Quick start

See [SETUP.md](./SETUP.md) for full instructions. Summary:

1. Create a Telegram bot via `@BotFather`, get the token and your chat ID
2. Set `TELEGRAM_CHAT_ID` in `custom-telegram.py`
3. Copy both scripts to `/var/ossec/integrations/`, set permissions/ownership
4. Install `requests` into Wazuh's Python: `/var/ossec/framework/python/bin/pip3 install requests`
5. Add an `<integration>` block to `ossec.conf` with your bot token as `api_key`
6. Restart `wazuh-manager`
7. Trigger a monitored file change and watch `/var/ossec/logs/integrations.log`

## Configuration

Alert filtering happens in two layers:

- **ossec.conf** — `<level>` sets the minimum alert severity forwarded to the script at all
- **`is_relevant_alert()`** in the Python script — restricts to specific rule groups (`syscheck`, `rootcheck`, `malware`, `virustotal`)

Adjust either layer depending on how noisy or targeted you want notifications
to be. For a graduation project demo, lowering `<level>` to `3` and testing
against a monitored file makes it easy to trigger and show working end-to-end.

## Extending

The script is structured so the alert-reading and filtering logic is
decoupled from the delivery mechanism:

- **Slack**: replace `send_telegram()` with a POST to a Slack Incoming Webhook using the `hook_url` argument Wazuh already passes
- **Email**: replace with `smtplib`/SMTP, no `api_key` needed
- **Other rule types**: adjust `relevant_groups` in `is_relevant_alert()` to match different alert categories (e.g. `authentication_failed` for brute-force detection)

## Troubleshooting

- Check `/var/ossec/logs/integrations.log` for script-level debug output
- Check `/var/ossec/logs/ossec.log` for Wazuh's own integration invocation errors
- Confirm the wrapper and script are executable and owned by `root:wazuh`
- Confirm `requests` is installed in Wazuh's bundled Python, not the system Python

## License

Educational/graduation project use.
