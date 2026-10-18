import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def predict_complaint(title, description):
    base_url = settings.ML_API_URL

    if not base_url:
        logger.error("ML_API_URL is not configured")
        return None

    url = f"{base_url}/predict"

    payload = {
        "title": title,
        "description": description,
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=90.0,
        )
        response.raise_for_status()

        result = response.json()

        if not isinstance(result, dict):
            raise ValueError("Invalid ML response format")

        if result.get("ml_available") is False:
            logger.warning("ML prediction is unavailable")
            return None

        return result

    except (httpx.HTTPError, ValueError):
        logger.exception("CampusPulse ML prediction failed")
        return None