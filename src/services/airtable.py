import json
import logging
from datetime import date
import requests
import boto3
from config.settings import settings_config

logger = logging.getLogger(__name__)

def upload_to_yandex_cloud(photo_path: str) -> str:
    # Создание клиента для Object Storage
    s3 = boto3.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

    # Имя бакета
    bucket_name = 'airtable-clone'

    # Загрузка фото
    local_photo_path = photo_path
    object_key = f'photos/{date.today()}_{photo_path}'
    s3.upload_file(local_photo_path, bucket_name, object_key)

    # Генерация временной ссылки на загруженный объект
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
        ExpiresIn=3600 * 24 * 30  # Ссылка действительна 30 дней
    )
    print("Временная ссылка на 30 дней:", url)

    return url


def send_to_airtable(action: str, data: dict, photo_path: str = None):
    """
    Отправляет данные в Airtable, упаковывая все поля в одну строку JSON.
    В самой Airtable это будет одним большим текстовым полем,
    которое можно обратно распарсить как JSON.
    """
    # Собираем в один словарь все исходные данные
    combined_data = {"action": action, **data}

    # Если есть фото, добавляем URL к combined_data
    if photo_path:
        photo_url = upload_to_yandex_cloud(photo_path)
        combined_data["photo_url"] = photo_url

    # Оборачиваем наш словарь в один JSON-объект, 
    # который будет отправлен в виде одного текстового поля all_data
    payload = {
        "all_data": json.dumps(combined_data, ensure_ascii=False)
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(settings_config.AIRTABLE_WEBHOOK, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Data sent to Airtable in single JSON field. Action: {action}")
        return True
    except Exception as e:
        logger.error(f"Error sending to Airtable: {e}", exc_info=True)
        return False
