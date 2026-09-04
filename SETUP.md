# Wazuh → Telegram Integration Setup

## 1. Get a Telegram bot token and chat ID
- Message `@BotFather` on Telegram → `/newbot` → copy the token
- Send any message to your bot, then visit:
  `https://api.telegram.org/bot<TOKEN>/getUpdates`
  → find `"chat":{"id": ...}` and copy that number

## 2. Edit the script
In `custom-telegram.py`, set:
```python
TELEGRAM_CHAT_ID = "123456789"   # your chat id
```

## 3. Install on the Wazuh manager
```bash
sudo cp custom-telegram.py /var/ossec/integrations/
sudo cp custom-telegram /var/ossec/integrations/

sudo chmod 750 /var/ossec/integrations/custom-telegram.py
sudo chmod 750 /var/ossec/integrations/custom-telegram
sudo chown root:wazuh /var/ossec/integrations/custom-telegram.py
sudo chown root:wazuh /var/ossec/integrations/custom-telegram

# Install the requests library into Wazuh's bundled Python
sudo /var/ossec/framework/python/bin/pip3 install requests
```

## 4. Register the integration in ossec.conf
Edit `/var/ossec/etc/ossec.conf` on the manager, add inside `<ossec_config>`:

```xml
<ossec_config>
  <integration>
    <name>custom-telegram</name>
    <api_key>YOUR_TELEGRAM_BOT_TOKEN</api_key>
    <alert_format>json</alert_format>
    <level>7</level>
  </integration>
</ossec_config>
```

- `level` = minimum alert severity to forward (7+ catches most FIM/malware alerts; lower it to test)
- To restrict strictly to syscheck/rootcheck groups, you can add `<group>syscheck,rootcheck</group>` instead of relying only on the Python-side filter

## 5. Restart the manager
```bash
sudo systemctl restart wazuh-manager
```

## 6. Test it
Trigger a FIM event by modifying a monitored file (e.g. one listed under `<syscheck>` in your agent's config), then check:
```bash
sudo tail -f /var/ossec/logs/integrations.log
sudo tail -f /var/ossec/logs/ossec.log | grep custom-telegram
```

## Adapting to Slack or email instead
- **Slack**: swap `send_telegram()` for a POST to your Slack Incoming Webhook URL (`hook_url` — Wazuh's 3rd argument — is exactly for this). Payload becomes `{"text": message}`.
- **Email**: replace with `smtplib` and send via your SMTP server; no api_key/hook_url needed, just SMTP credentials (best stored in the script or environment, not ossec.conf).

Both variants keep the same `read_alert()` / `is_relevant_alert()` / `format_message()` structure — only the "send" function changes.
