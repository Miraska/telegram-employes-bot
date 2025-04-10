import json
import requests
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

def send_to_airtable(action: str, employee_data: dict):
    print('Отправка данных в Airtable')
    payload = {
        "action": action,
        **employee_data
    }
    
    try:
        print('Отправка данных в Airtable в блоке try')
        headers = {
            "Content-Type": "application/json"
        }

        # Сериализуем payload в строку JSON
        payload_as_text = json.dumps(payload, ensure_ascii=False)

        # Отправляем запрос, где ключ "raw_json" содержит JSON как текст
        body = {
            "raw_json": payload_as_text
        }

        response = requests.post(
            settings.AIRTABLE_WEBHOOK,
            json=body,
            headers=headers
        )

        # Для отладки выведем текст ответа (или код статуса)
        print("Response code:", response.status_code)
        print("Response body:", response.text)

        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке в Airtable: {e}", exc_info=True)
        return False
