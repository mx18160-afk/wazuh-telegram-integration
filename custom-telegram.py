#!/usr/bin/env python3
"""
Wazuh Custom Integration: Send FIM / Malware alerts to Telegram
------------------------------------------------------------
Install:
  1. Copy this file to:      /var/ossec/integrations/custom-telegram.py
  2. Copy the wrapper below to: /var/ossec/integrations/custom-telegram
  3. chmod +x both files, chown to wazuh:wazuh
  4. Add the <integration> block (see bottom of this file) to ossec.conf
  5. Restart wazuh-manager

Wazuh calls this script as:
    custom-telegram.py <alert_file> <api_key> <hook_url>

- alert_file : path to a JSON file containing the alert Wazuh generated
- api_key    : your Telegram bot token (passed from ossec.conf <api_key>)
- hook_url   : not used for Telegram, but Wazuh always passes 3 args;
               we ignore it here (kept for signature compatibility)
"""

import json
import sys
import time
import requests

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"     # numeric chat/group id
LOG_FILE = "/var/ossec/logs/integrations.log"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def log(msg):
    """Write debug info to Wazuh's integrations log so you can troubleshoot."""
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} custom-telegram: {msg}\n")
    except Exception:
        pass  # never let logging crash the integration


def read_alert(alert_file_path):
    with open(alert_file_path) as f:
        return json.load(f)


def is_relevant_alert(alert):
    """
    Filter: only forward FIM (syscheck) and malware/rootcheck related alerts.
    Adjust rule group / id logic here to match what you actually want.
    """
    rule = alert.get("rule", {})
    groups = rule.get("groups", [])
    relevant_groups = {"syscheck", "rootcheck", "malware", "virustotal"}
    return bool(relevant_groups.intersection(groups))


def format_message(alert):
    rule = alert.get("rule", {})
    agent = alert.get("agent", {})
    syscheck = alert.get("syscheck", {})

    lines = [
        "🛡️ *Wazuh Security Alert*",
        f"*Level:* {rule.get('level', 'N/A')}",
        f"*Description:* {rule.get('description', 'N/A')}",
        f"*Agent:* {agent.get('name', 'N/A')} ({agent.get('id', 'N/A')})",
        f"*Time:* {alert.get('timestamp', 'N/A')}",
    ]

    if syscheck:
        lines.append(f"*File:* `{syscheck.get('path', 'N/A')}`")
        event = syscheck.get("event")
        if event:
            lines.append(f"*Event:* {event}")
        sha1_after = syscheck.get("sha1_after")
        if sha1_after:
            lines.append(f"*SHA1:* `{sha1_after}`")

    lines.append(f"*Rule ID:* {rule.get('id', 'N/A')}")
    return "\n".join(lines)


def send_telegram(bot_token, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                log("Message sent successfully.")
                return True
            else:
                log(f"Attempt {attempt}: Telegram API returned {resp.status_code}: {resp.text}")
        except requests.RequestException as e:
            log(f"Attempt {attempt}: request failed: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    return False


def main():
    if len(sys.argv) < 3:
        log("ERROR: insufficient arguments passed by Wazuh.")
        sys.exit(1)

    alert_file = sys.argv[1]
    bot_token = sys.argv[2]
    # sys.argv[3] would be hook_url, unused for Telegram

    try:
        alert = read_alert(alert_file)
    except Exception as e:
        log(f"ERROR reading alert file: {e}")
        sys.exit(1)

    if not is_relevant_alert(alert):
        log("Alert did not match filter (not FIM/malware/rootcheck) - skipped.")
        sys.exit(0)

    message = format_message(alert)
    success = send_telegram(bot_token, message)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
