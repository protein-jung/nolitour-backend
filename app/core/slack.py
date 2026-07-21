import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_slack_alert(message: str) -> None:
    """Best-effort Slack webhook notification. Never raises."""
    if not settings.slack_webhook_url:
        return
    try:
        httpx.post(settings.slack_webhook_url, json={"text": message}, timeout=5)
    except httpx.HTTPError:
        logger.warning("Failed to send Slack alert", exc_info=True)
