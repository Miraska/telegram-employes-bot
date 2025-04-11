import requests
import logging
from config.settings import settings_config

logger = logging.getLogger(__name__)

def upload_to_imgur(photo_path: str, client_id: str) -> str:
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {client_id}"}
    with open(photo_path, "rb") as photo_file:
        response = requests.post(url, headers=headers, files={"image": photo_file})
        response.raise_for_status()
        data = response.json()
        return data["data"]["link"]

def send_to_airtable(action: str, data: dict, photo_path: str = None):
    payload = {"action": action, **data}
    headers = {"Content-Type": "application/json"}

    if photo_path:
        imgur_client_id = "YOUR_IMGUR_CLIENT_ID"  # Замените на ваш Client ID
        photo_url = upload_to_imgur(photo_path, imgur_client_id)
        payload["photo_url"] = photo_url
        try:
            response = requests.post(settings_config.AIRTABLE_WEBHOOK, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Data sent to Airtable: {action}")
            return True
        except Exception as e:
            logger.error(f"Error sending to Airtable: {e}", exc_info=True)
            return False
    else:
        try:
            response = requests.post(settings_config.AIRTABLE_WEBHOOK, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Data sent to Airtable: {action}")
            return True
        except Exception as e:
            logger.error(f"Error sending to Airtable: {e}", exc_info=True)
            return False