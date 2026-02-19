import os
import json
import requests


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_ALERT_ON_STARTUP = os.getenv("SLACK_ALERT_ON_STARTUP", "false").lower() == "true"
SLACK_ALERT_ON_MESSAGE = os.getenv("SLACK_ALERT_ON_MESSAGE", "false").lower() == "true"


def _post_to_slack(payload: dict):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        headers = {"Content-Type": "application/json"}
        requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(payload), timeout=5)
    except Exception:
        # Slack failures should never break the worker
        pass


def send_startup_alert(text: str, extra: dict | None = None):
    if not SLACK_ALERT_ON_STARTUP:
        return
    payload = {
        "text": text,
    }
    if extra:
        attachments = [
            {
                "color": "#36a64f",
                "fields": [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in extra.items()
                ],
            }
        ]
        payload["attachments"] = attachments
    _post_to_slack(payload)


def send_message_alert(text: str, extra: dict | None = None):
    if not SLACK_ALERT_ON_MESSAGE:
        return
    payload = {
        "text": text,
    }
    if extra:
        attachments = [
            {
                "color": "#439FE0",
                "fields": [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in extra.items()
                ],
            }
        ]
        payload["attachments"] = attachments
    _post_to_slack(payload)
